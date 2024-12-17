import os
import shutil
import sys
import util
import time
import os
import sys
import utils_docker
import json

here = os.path.abspath(os.path.dirname(__file__))

# create env.py file if this is the first run
util.initializeFiles()

print("Reading env.py")
import env

print("Applying env var substitutions in hard-coded .template files")
util.substitutions(here, env)
util.writeViteEnv(vars(env))

if not os.path.isdir(env.keys_dir):
    os.system("cd certs && ./init-temp-keys.cmd")

# Convert env.py to a dictionary
config = vars(env)
# make sure the network is up
utils_docker.ensure_network(env.BRAND_NAME)

# create the keys if they dont exist
if not os.path.isdir("certs/keys"):
    os.system("cd certs && ./init-temp-keys.sh")

# --- WEB APP ---
# theoretically has no dependencies
utils_docker.run_container(env.webapp)

# --- KEYCLOAK ---
utils_docker.run_container(env.keycloakdb)
utils_docker.wait_for_db(network=env.BRAND_NAME, db_url="keycloakdb:5432")
utils_docker.run_container(env.keycloak)

# --- NGINX ---
if not os.path.isfile("certs/ca.crt"):
    if env.IS_EC2:
        utils_docker.generateProdKeys(outdir=env.certs_dir, website=env.USER_WEBSITE)
    else:
        utils_docker.generateDevKeys(outdir=env.certs_dir)
utils_docker.run_container(env.nginx)

# --- OPENTDF ---
utils_docker.run_container(env.opentdfdb)
utils_docker.wait_for_db(network=env.BRAND_NAME, db_url="opentdfdb:5432")
utils_docker.wait_for_url(env.KEYCLOAK_INTERNAL_AUTH_URL, network=env.BRAND_NAME)
utils_docker.run_container(env.opentdf)

# --- ORG ---
utils_docker.run_container(env.org)

# --- MATRIX SYNAPSE ---
utils_docker.run_container(env.synapsedb)
utils_docker.wait_for_db(network=env.BRAND_NAME, db_url="synapsedb:5432")
utils_docker.run_container(env.synapse)

# --- OLLAMA !!! ---
utils_docker.run_container(env.ollama)

models_to_pull = ["llama3.2", "ALIENTELLIGENCE/sigmundfreud"]
for model_name in models_to_pull:
    if not utils_docker.model_exists(model_name):
        print(f"Pulling model: {model_name}")
        utils_docker.run_container(
            dict(
                image="curlimages/curl",
                name="ModelPull",
                command=[
                    "curl",
                    "-X",
                    "POST",
                    "http://localhost:11434/api/pull",
                    "-d",
                    json.dumps({"model": model_name}),
                ],
                network_mode="host",
                remove=True,
                detach=False,
            )
        )
    else:
        print(f"Model {model_name} already exists locally")

# to test a model
# curl http://localhost:11434/api/chat -d '{"model": "llama3.2", "messages": [{"role": "user", "content": "How are you?"}]}' | jq
