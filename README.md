# Semantic Embeddings with ChatGPT
This project uses **[Zep](https://github.com/getzep/zep)**, a semantic embeddings database, to power a ChatGPT conversational platform that is able to entertain Q&A style conversation with chat context recall and semantic embedding search for better contextual responses. See this [blog](https://matrixmaster.me/blog/2023/embedding-gpt/) post for more information on the theory and implementation.

## Deployment
First, clone the repo with:
```sh
git clone https://github.com/TheMatrixMaster/gpt-embeddings
``` 

Then you will need to pull the `zep` submodule using the following command from the project root
```sh
cd gpt-embeddings
git submodule update --init
```


### Adding secret keys and seed data
First, we need to create a few `.env` files, so that both the frontend and backend have access to gpt models for conversation and embedding, respectively.

Please create the following file `zep/.env` and populate it with the following keys:

```.env
ZEP_OPENAI_API_KEY="<OPENAI API KEY>"
ZEP_LLM_OPENAI_ORG_ID="OPTIONAL OPENAI ORG"
```

Then, create another env file in the following path `web/.env` and populate it with the same key values. Notice that the key name has changed though.

```.env
OPENAI_API_KEY="OPENAI API KEY"
OPENAI_ORGANIZATION="OPTIONAL OPENAI ORG"
```

Finally, we need to create a few documents that the database can embed into search vectors for the context retrieval. Please create a new directory in the repo root named `documents/` and create a file in there named `documents/raw_convo.txt`. (TODO: add support for auto-chunking any text, json, or yml documents)

### Deploy from docker
Once the above steps have been completed, you should be able to start the service on your machine by running the following command from the project root. Make sure you have `docker` and `docker-compose` installed.

```sh
docker compose up
```