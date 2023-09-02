import { env } from '$env/dynamic/private';
import { OPENAI_API_KEY, OPENAI_ORGANIZATION } from "$env/static/private";
import { ChatOpenAI } from "langchain/chat_models/openai";

import { ConversationalRetrievalQAChain } from "langchain/chains";

import { ZepVectorStore } from "langchain/vectorstores/zep";
import type { IZepConfig } from "langchain/vectorstores/zep";

import { FakeEmbeddings } from "langchain/embeddings/fake";
import { BufferMemory } from "langchain/memory";

import { error } from '@sveltejs/kit';

export type MessageBody = { 
    question: string;
    settings: { temperature: number, relatedness: number };
}

const zepConfig: IZepConfig = {
    apiUrl: env.ZEP_SERVER_URL ?? "http://localhost:8000", // the URL of your Zep implementation
    collectionName: "fever",  // the name of your collection. alphanum values only
};

const CUSTOM_QUESTION_GENERATOR_CHAIN_PROMPT = `
    Given the following conversation and a follow up question,
    return the conversation history excerpt that includes any relevant context to the question
    if it exists and rephrase the follow up question to be a standalone question.
    
    Chat History: {chat_history}
    Follow Up Input: {question}
    
    Your answer should follow the following format:

    \`\`\`
    You are a medical assistant that provides factual information about fevers and 
    fever-related symptoms. Answer with markdown where appropriate. Your tone as an 
    assistant is to be reassuring to the user without ever giving false information.
    Do not answer questions that are unrelated to fevers or fever-related symptoms.
    
    Use the following pieces of context to answer the users question.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    ----------------
    <Relevant chat history excerpt as context here>
    Standalone question: <Rephrased question here>
    \`\`\`

    Your answer:
`;

const embeddings = new FakeEmbeddings();

export const POST = async ({ request }) => {
    const body: MessageBody = await request.json();

    if (!body) throw error(400, 'Missing Data');

    // Connect to the Zep vector store server
    const vectorStore = await new ZepVectorStore(embeddings, zepConfig);

    // Create a new readable stream of the chat response
    const readableStream = new ReadableStream({
        async start(controller) {
            // Create a new chat model
            const streamingModel = new ChatOpenAI({
                openAIApiKey: OPENAI_API_KEY,
                modelName: "gpt-4",
                streaming: true,
                temperature: body.settings.temperature,
                callbacks: [{
                    handleLLMNewToken: async (token: string) => controller.enqueue(token),
                }]
            }, {
                organization: OPENAI_ORGANIZATION,
            });

            const nonStreamingModel = new ChatOpenAI({
                openAIApiKey: OPENAI_API_KEY,
                modelName: "gpt-3.5-turbo",
                temperature: body.settings.temperature,
            }, {
                organization: OPENAI_ORGANIZATION,
            });

            const chain = ConversationalRetrievalQAChain.fromLLM(
                streamingModel,
                vectorStore.asRetriever({
                    vectorStore: vectorStore,
                    verbose: true,
                }),
                {
                    memory: new BufferMemory({
                        memoryKey: "chat_history", // Must be set to "chat_history"
                        inputKey: "question", // The key for the input to the chain
                        outputKey: "text", // The key for the final conversational output of the chain
                        returnMessages: true, // If using with a chat model
                    }),
                    returnSourceDocuments: true,
                    questionGeneratorChainOptions: {
                        llm: nonStreamingModel,
                        template: CUSTOM_QUESTION_GENERATOR_CHAIN_PROMPT
                    },
                },
            );

            const question = body.question;
            if (!question) throw error(400, 'Missing Question');

            const resp = await chain.call({ question });
            controller.close();
        },
    });

    // Create and return a response of the readable stream
    return new Response(readableStream, {
        headers: {
            'Content-Type': 'text/plain',
        },
    });
}



