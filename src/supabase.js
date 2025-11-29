import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://dostficclwnmxkiqstix.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRvc3RmaWNjbHdubXhraXFzdGl4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzOTQwMTMsImV4cCI6MjA3OTk3MDAxM30.AV_A6snml27gv2cCWNQ3lP8QgceM5MeGtJxeF8zy1tI';

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  db: {
    schema: 'public'
  }
});
