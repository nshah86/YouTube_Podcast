import os
import time
import random
import re
from gtts import gTTS
from ..config.settings import DEFAULT_LANGUAGE_CODE

def text_to_speech(text: str, output_file: str, gender: str = "mixed") -> None:
    """
    Convert text to speech and save as an audio file.
    
    This function currently uses gTTS for text-to-speech conversion.
    In the future, it could be extended to use ElevenLabs or other TTS services.
    
    Args:
        text: The text to convert to speech
        output_file: Path where the audio file will be saved
        gender: Voice gender preference (male, female, or mixed)
        
    Returns:
        None. The audio file is saved to the specified output path.
    """
    # Format the conversation text to be more suitable for TTS
    # Clean and process the text for more natural speech
    lines = text.split('\n')
    processed_lines = []
    current_speaker = None
    last_speaker = None
    
    for line in lines:
        if not line.strip():
            continue
            
        if ':' in line:
            # Extract the speaker and content
            parts = line.split(':', 1)
            speaker = parts[0].strip()
            content = parts[1].strip() if len(parts) > 1 else ""
            
            # Clean the content - remove asterisks, excessive punctuation
            content = clean_text_for_speech(content)
            
            # Add natural transitions between speakers
            if last_speaker and speaker != last_speaker:
                processed_lines.append("<break time='1s'/>")
            
            # Format with conversational introduction
            if speaker != current_speaker:
                # Only add speaker introduction when the speaker changes
                if gender == "male":
                    voice_intro = f"{speaker} says, "
                elif gender == "female":
                    voice_intro = f"Then {speaker} responds, "
                else:
                    voice_intro = f"{speaker} says, "
                processed_lines.append(voice_intro + content)
                current_speaker = speaker
            else:
                # Continue with the same speaker
                processed_lines.append(content)
            
            last_speaker = speaker
        else:
            # Lines without a speaker
            processed_lines.append(clean_text_for_speech(line))
    
    # Join the processed lines with natural pauses
    processed_text = " ".join(processed_lines)
    
    # Add SSML tags for more natural speech if needed
    processed_text = add_speech_enhancements(processed_text)
    
    # Create and save the audio file using gTTS
    try:
        tts = gTTS(text=processed_text, lang=DEFAULT_LANGUAGE_CODE, slow=False)
        tts.save(output_file)
        
        # Verify the file was created
        if not os.path.exists(output_file):
            raise FileNotFoundError(f"Failed to create audio file at {output_file}")
            
        # Small delay to ensure file is written completely
        time.sleep(0.5)
        
    except Exception as e:
        raise Exception(f"TTS generation failed: {str(e)}")

def clean_text_for_speech(text: str) -> str:
    """
    Clean text to make it more suitable for speech synthesis.
    
    Args:
        text: The text to clean
        
    Returns:
        Cleaned text optimized for speech
    """
    # Remove markdown-style formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
    text = re.sub(r'__(.*?)__', r'\1', text)      # Underline
    text = re.sub(r'~~(.*?)~~', r'\1', text)      # Strikethrough
    
    # Replace special characters that might be read literally
    text = text.replace('&', 'and')
    text = text.replace('/', ' or ')
    text = text.replace('#', 'number ')
    text = text.replace('@', 'at ')
    text = text.replace('...', '.')  # Replace ellipsis with period for cleaner pauses
    text = text.replace('—', ', ')   # Em dash
    text = text.replace('–', ', ')   # En dash
    text = text.replace('|', ', ')   # Vertical bar
    
    # Convert common abbreviations
    text = re.sub(r'\bi\.e\.\s', 'that is, ', text, flags=re.IGNORECASE)
    text = re.sub(r'\be\.g\.\s', 'for example, ', text, flags=re.IGNORECASE)
    text = re.sub(r'\betc\.', 'etcetera', text, flags=re.IGNORECASE)
    text = re.sub(r'\bvs\.', 'versus', text, flags=re.IGNORECASE)
    
    # Convert URLs to more speech-friendly format
    text = re.sub(r'https?://\S+', 'a website link', text)
    
    # Replace multiple punctuations with single ones
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'\!{2,}', '!', text)
    text = re.sub(r'\?{2,}', '?', text)
    
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Ensure proper spacing around punctuation
    text = re.sub(r'(\w)([,.!?;:])', r'\1\2 ', text)
    text = re.sub(r'\s+([,.!?;:])', r'\1 ', text)
    
    # Replace dashes with natural pauses
    text = text.replace(' - ', ', ')
    
    # Make quoted content more natural for speech
    text = re.sub(r'"([^"]*)"', r' \1 ', text)
    text = re.sub(r"'([^']*)'", r' \1 ', text)
    
    return text.strip()

def add_speech_enhancements(text: str) -> str:
    """
    Add enhancements to make speech more natural.
    
    Args:
        text: Processed text
        
    Returns:
        Enhanced text for more natural speech
    """
    # Add natural pauses for commas and periods
    text = text.replace('. ', '. <break time="0.3s"/> ')
    text = text.replace('? ', '? <break time="0.5s"/> ')
    text = text.replace('! ', '! <break time="0.4s"/> ')
    
    # Remove any SSML tags that gTTS doesn't support
    text = re.sub(r'<break[^>]*>', '', text)
    
    return text 