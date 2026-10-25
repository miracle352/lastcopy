export function GET() {
  return Response.json({service: "lastcopy-web", status: "ok", evidence_backend: process.env.LASTCOPY_CLOUD_ACCESS==='true' ? "authenticated_cloud_configured" : process.env.VERCEL ? "not_deployed" : "separate_local_service",live_verified:false});
}
