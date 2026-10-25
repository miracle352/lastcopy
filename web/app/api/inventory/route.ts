import { backendOrigin, localRequest,upstreamHeaders } from "../../../lib/backend";
export const dynamic = "force-dynamic";
export async function GET(request:Request) {
  if(!localRequest(request))return Response.json({error:'Use the local LastCopy host'},{status:403});
  const origin = backendOrigin();
  if (!origin) return Response.json({error: "Private API unavailable in hosted skeleton"}, {status: 503});
  try {
    const result = await fetch(`${origin}/sample/inventory`, {cache: "no-store",redirect:'error',headers:upstreamHeaders(request), signal: AbortSignal.timeout(5000)});
    if (!result.ok) return Response.json({error: "API unavailable or incompatible mode"}, {status: result.status === 409 ? 409 : 503});
    return Response.json(await result.json());
  } catch { return Response.json({error: "Start the local API on port 8000"}, {status: 503}); }
}
