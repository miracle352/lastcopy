export function GET() {
  return Response.json({service: "lastcopy-web", status: "ok", stage: 1, evidence_backend: process.env.VERCEL ? "not_deployed" : "separate_local_service", live_verified: false});
}
