// index.js (Temporary file to force route detection)
export default {
    async fetch(request, env, ctx) {
        return new Response("Hello from temporary JS worker!", { status: 200 });
    },
};