import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://fvggzvuijvqumajaydpt.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ2Z2d6dnVpanZxdW1hamF5ZHB0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzNzY0NDQsImV4cCI6MjA3OTk1MjQ0NH0.cjC1vDZsV8ZTkwusI2cR6EILKojedKrfLUHN9-4g8Ec';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
