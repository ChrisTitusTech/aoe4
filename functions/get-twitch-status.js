export async function onRequest(context) {
  const channelName = 'House_of_Titus';
  const clientId = 'za4ggow0vi8blxkh1hh4m96hf94a6h';
  
  // Fetch the bearer token from KV
  const bearerToken = await context.env.TWITCH_KV.get('bearer_token');

  if (!bearerToken) {
    return new Response(JSON.stringify({ error: 'Bearer token not found' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  try {
    const response = await fetch(`https://api.twitch.tv/helix/streams?user_login=${channelName}`, {
      headers: {
        'Client-ID': clientId,
        'Authorization': `Bearer ${bearerToken}`
      }
    });

    const data = await response.json();
    const isLive = data.data && data.data.length > 0;

    return new Response(JSON.stringify({ isLive }), {
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to check Twitch status' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
