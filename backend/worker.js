// PL Radar — proxy sperimentale ViaggiaTreno (Cloudflare Worker).
// Non stima lo stato delle sbarre e non garantisce dati su treni merci.
const VT = "https://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/";
const ALLOWED = ["Palma", "Nola", "Sarno"];
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const headers = {
      "Access-Control-Allow-Origin": env.ALLOWED_ORIGIN || "https://salvo1984.github.io",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Cache-Control": "no-store",
      "Content-Type": "application/json; charset=utf-8"
    };
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers });
    if (request.method !== "GET" || url.pathname !== "/api/stations") return new Response(JSON.stringify({error:"Not found"}),{status:404,headers});
    const query = url.searchParams.get("q") || "";
    if (!ALLOWED.includes(query)) return new Response(JSON.stringify({error:"Query not allowed",allowed:ALLOWED}),{status:400,headers});
    try {
      const upstream = await fetch(VT + "autocompletaStazione/" + encodeURIComponent(query), {
        headers: { "Accept": "text/plain" },
        signal: AbortSignal.timeout(10000)
      });
      const body = await upstream.text();
      if (!upstream.ok) return new Response(JSON.stringify({error:"Upstream error",status:upstream.status}),{status:502,headers});
      return new Response(JSON.stringify({query,raw:body.slice(0,12000),source:"ViaggiaTreno non ufficiale",verified:false}),{status:200,headers});
    } catch (e) {
      return new Response(JSON.stringify({error:"Upstream unavailable",detail:String(e.message||e)}),{status:502,headers});
    }
  }
};
