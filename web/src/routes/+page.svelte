<script lang="ts">
    import { readablestreamStore, settings } from "$lib/readablestreamstore";
    import { markdownParser } from "$lib/markdownparser";
    import { fly } from "svelte/transition";

    import Typingindicator from "$lib/typingindicator.svelte";

    let isPanelOpen: boolean = true;
    const response = readablestreamStore();

    let chat_history: { role: "user" | "assistant"; content: string }[] = [];

    function togglePanel() {
        isPanelOpen = !isPanelOpen;
    }

    async function handleSubmit(this: HTMLFormElement) {
        if ($response.loading) return;

        const formData: FormData = new FormData(this);
        const message = formData.get("message") as string;

        if (message == "") return;

        chat_history = [...chat_history, { role: "user", content: message }];

        try {
            const answer = response.request(
                new Request("/api/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        question: message,
                        settings: $settings,
                    }),
                })
            );

            this.reset();

            chat_history = [...chat_history, { role: "assistant", content: (await answer) as string }];
        } catch (err) {
            chat_history = [...chat_history, { role: "assistant", content: `Error: ${err}` }];
        }
    }
</script>

<main class="flex flex-row py-4 gap-10">
    <div class="flex flex-col">
        <div class="flex flex-col space-y-2 pb-2">
            <h1 class="text-3xl font-bold underline">Chat!</h1>
            <p>Example made for <i><b>SickKids</b></i>.</p>
        </div>

        <form class="chat-wrapper" on:submit|preventDefault={handleSubmit} method="POST" action="/api/chat">
            <div class="flex flex-col space-y-2 overflow-y-auto w-full aspect-square text-sm">
                {#await new Promise((res) => setTimeout(res, 400)) then _}
                    <div class="flex">
                        <div in:fly={{ y: 50, duration: 400 }} class="assistant-chat">
                            Hello! I am a chatbot that answers questions about fever in children.
                        </div>
                    </div>
                {/await}

                {#each chat_history as chat}
                    {#if chat.role == "user"}
                        <div class="flex justify-end">
                            <div in:fly={{ y: 50, duration: 600 }} class="user-chat">
                                {#await markdownParser(chat.content)}
                                    {chat.content}
                                {:then html}
                                    {@html html}
                                {/await}
                            </div>
                        </div>
                    {:else}
                        <div class="flex">
                            <div in:fly={{ y: 50, duration: 600 }} class="assistant-chat">
                                {#await markdownParser(chat.content)}
                                    {chat.content}
                                {:then html}
                                    {@html html}
                                {/await}
                            </div>
                        </div>
                    {/if}
                {/each}

                {#if $response.loading}
                    {#await new Promise((res) => setTimeout(res, 400)) then _}
                        <div class="flex">
                            <div in:fly={{ y: 50, duration: 600 }} class="assistant-chat">
                                {#if $response.text == ""}
                                    <Typingindicator />
                                {:else}
                                    {#await markdownParser($response.text)}
                                        {$response.text}
                                    {:then html}
                                        {@html html}
                                    {/await}
                                {/if}
                            </div>
                            {#if $response.text != ""}
                                <div class="w-2" />
                                <div class="w-4 m-1">
                                    <svg class="animate-spin h-4 w-4 text-neutral-600 dark:text-neutral-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                    </svg>
                                </div>
                            {/if}
                        </div>
                    {/await}
                {/if}
            </div>

            <div class="h-px bg-gray-200" />

            <span class="flex flex-row space-x-4">
                <input type="text" placeholder="Type your message..." name="message" class="chat-message" />
                <button type="submit" class="chat-send"> Send </button>
            </span>
        </form>
    </div>
    <div class="panel-wrapper">
        <div class="flex flex-col space-y-1">
            <div class="flex flex-row justify-between">
                <h1 class="text-2xl font-bold underline">Control Panel</h1>
                <button class="chat-send" on:click={togglePanel}> {isPanelOpen ? 'Hide' : 'Show'} </button>
            </div>
            <p class="text-sm">Use the controls in this panel to configure the llm.</p>
        </div>
        <div class="panel-wrapper space-y-3 py-3" style={`display: ${isPanelOpen ? 'unset' : 'none'}`}>
            <div class="flex flex-col">
                <h2 class="text-lg font-bold">Model Temperature</h2>
                <p class="text-xs">A higher temperature allows the model to sample reponses with a higher variance.</p>
                <div class="flex flex-row pt-2 w-full space-x-5">
                    <input
                        class="w-full"
                        type="range"
                        min="0.0"
                        max="1.0"
                        step="0.01"
                        bind:value={$settings.temperature}
                    />
                    <p class="text-lg">{$settings.temperature}</p>
                </div>
            </div>
            <div class="flex flex-col">
                <h2 class="text-lg font-bold">Top-K documents</h2>
                <p class="text-xs">Only allows the model to use the top K most relevant documents during inference.</p>
                <div class="flex flex-row pt-2 w-full space-x-5">
                    <input
                        class="w-full"
                        type="range"
                        min="0"
                        max="100"
                        step="1"
                        bind:value={$settings.relatedness}
                    />
                    <p class="text-lg">{$settings.relatedness}</p>
                </div>
            </div>
        </div>
        <div class="flex flex-col space-y-1 pt-2">
            <h1 class="text-2xl font-bold underline">Reference Panel</h1>
            <p class="text-sm">This panel will display the vector embeddings used by the model to sample the latest response.</p>
        </div>
        <div class="panel-wrapper space-y-3 py-3">
            
        </div>
    </div>
</main>

<style lang="postcss">
    .chat-wrapper {
        @apply flex flex-col space-y-4 md:min-w-[26rem] lg:min-w-[30rem] xl:min-w-[34rem] max-w-6xl;
    }

    .panel-wrapper {
        @apply flex flex-col md:max-w-[22rem] lg:max-w-[26rem] xl:max-w-[30rem];
    }

    .assistant-chat {
        @apply bg-gray-200 text-gray-800 rounded-lg px-4 py-2 max-w-xs my-0 prose prose-sm prose-pre:font-mono prose-pre:border prose-pre:bg-white prose-code:border-gray-300;
    }

    .user-chat {
        @apply bg-[#FF3E00] text-white rounded-lg px-4 py-2 max-w-xs my-0 prose prose-sm prose-pre:font-mono prose-pre:border prose-pre:bg-white prose-code:border-gray-300;
    }

    .chat-message {
        @apply block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-black sm:text-sm sm:leading-6;
    }

    .chat-send {
        @apply block items-center rounded-md border border-transparent bg-neutral-800 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-black focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2;
    }
</style>
