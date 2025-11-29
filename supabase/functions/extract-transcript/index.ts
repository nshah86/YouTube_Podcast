import { createClient } from 'npm:@supabase/supabase-js@2.39.0';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Client-Info, Apikey',
};

interface TranscriptSegment {
  text: string;
  start: number;
  duration: number;
}

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: corsHeaders,
    });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL') || '';
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || '';
    const supabase = createClient(supabaseUrl, supabaseKey);

    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
      throw new Error('Missing authorization header');
    }

    const token = authHeader.replace('Bearer ', '');
    const { data: { user }, error: authError } = await supabase.auth.getUser(token);

    if (authError || !user) {
      throw new Error('Unauthorized');
    }

    const { videoId } = await req.json();

    if (!videoId) {
      throw new Error('Missing videoId parameter');
    }

    const transcriptUrl = `https://youtube-transcript3.p.rapidapi.com/transcript?videoId=${videoId}&lang=en`;
    
    const rapidApiKey = Deno.env.get('RAPIDAPI_KEY');
    
    if (!rapidApiKey) {
      const fallbackUrl = `https://www.youtube.com/watch?v=${videoId}`;
      const ytResponse = await fetch(fallbackUrl);
      const html = await ytResponse.text();
      
      const captionsMatch = html.match(/"captions":\{[^}]+"playerCaptionsTracklistRenderer":\{"captionTracks":\[([^\]]+)\]/);
      
      if (!captionsMatch) {
        throw new Error('No captions available for this video');
      }
      
      const captionTracksMatch = captionsMatch[0].match(/"baseUrl":"([^"]+)"/);
      if (!captionTracksMatch) {
        throw new Error('Could not find caption URL');
      }
      
      const captionUrl = captionTracksMatch[1].replace(/\\u0026/g, '&');
      const captionResponse = await fetch(captionUrl);
      const captionXml = await captionResponse.text();
      
      const textMatches = captionXml.matchAll(/<text[^>]*start="([^"]+)"[^>]*dur="([^"]+)"[^>]*>([^<]+)<\/text>/g);
      const transcript: TranscriptSegment[] = [];
      
      for (const match of textMatches) {
        transcript.push({
          start: parseFloat(match[1]),
          duration: parseFloat(match[2]),
          text: match[3]
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'")
            .replace(/<[^>]+>/g, '')
        });
      }
      
      return new Response(
        JSON.stringify({
          success: true,
          videoId,
          transcript,
          title: 'YouTube Video'
        }),
        {
          headers: {
            ...corsHeaders,
            'Content-Type': 'application/json',
          },
        }
      );
    }

    const response = await fetch(transcriptUrl, {
      headers: {
        'X-RapidAPI-Key': rapidApiKey,
        'X-RapidAPI-Host': 'youtube-transcript3.p.rapidapi.com'
      }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch transcript from YouTube');
    }

    const data = await response.json();

    return new Response(
      JSON.stringify({
        success: true,
        videoId,
        transcript: data.transcript || data,
        title: data.title || 'YouTube Video'
      }),
      {
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );

  } catch (error) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message || 'Failed to extract transcript'
      }),
      {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );
  }
});