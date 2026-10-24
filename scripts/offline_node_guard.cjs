/* Audit-only fence for the production Next process; never enabled in normal use. */
const net=require('node:net');
function local(host){return !host||['localhost','127.0.0.1','::1'].includes(host);}
const connect=net.Socket.prototype.connect;
net.Socket.prototype.connect=function(...args){
  const first=Array.isArray(args[0])?args[0][0]:args[0];
  const host=typeof first==='object'?first?.host:typeof args[1]==='string'?args[1]:undefined;
  if(!local(host))throw new Error('Offline audit blocks non-loopback networking');
  return connect.apply(this,args);
};
const nativeFetch=globalThis.fetch;
globalThis.fetch=function(input,...args){const url=new URL(typeof input==='string'||input instanceof URL?input:input.url);if(!local(url.hostname))return Promise.reject(new Error('Offline audit blocks external fetch'));return nativeFetch(input,...args);};
