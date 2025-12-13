"""
Image Generation for Token Metadata
Auto-generates token logos for Pump.fun deployments
"""

import os
import logging
import requests
from typing import Optional
from pathlib import Path
from io import BytesIO

logger = logging.getLogger(__name__)


class TokenImageGenerator:
    """
    Generate token images for metadata.
    Supports multiple backends: OpenAI DALL-E, Stability AI, and local generation.
    """
    
    def __init__(self):
        """Initialize image generator with available backends"""
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.stability_key = os.getenv("STABILITY_API_KEY")
        
        # Determine available backends
        self.backends = []
        if self.openai_key:
            self.backends.append("openai")
        if self.stability_key:
            self.backends.append("stability")
        self.backends.append("local")  # Always available
        
        logger.info(f"Image generator initialized with backends: {', '.join(self.backends)}")
    
    def generate(
        self,
        token_name: str,
        token_symbol: str,
        description: str = "",
        style: str = "memecoin",
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate token image.
        
        Args:
            token_name: Name of the token
            token_symbol: Token ticker symbol
            description: Token description
            style: Visual style (memecoin, professional, crypto, pepe, etc)
            output_path: Where to save image (default: ./data/images/)
        
        Returns:
            Path to generated image or None if failed
        """
        try:
            # Setup output path
            if not output_path:
                output_dir = Path("./data/images")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"{token_symbol.lower()}_logo.png")
            
            logger.info(f"Generating image for {token_name} ({token_symbol})")
            
            # ALWAYS try DALL-E first if API key is available
            if self.openai_key:
                logger.info("🎨 Using DALL-E 3 for professional AI generation...")
                result = self._generate_openai(token_name, token_symbol, description, style, output_path)
                if result:
                    logger.info("✅ Successfully generated with DALL-E 3")
                    return result
                else:
                    logger.warning("⚠️ DALL-E 3 failed, falling back to local generation")
            
            # Try Stability AI if available
            if self.stability_key:
                logger.info("Trying Stability AI...")
                result = self._generate_stability(token_name, token_symbol, description, style, output_path)
                if result:
                    return result
            
            # Fallback to local generation only if AI fails
            logger.info("Using local PIL generator as fallback...")
            result = self._generate_local(token_name, token_symbol, style, output_path)
            if result:
                return result
            
            logger.error("All image generation backends failed")
            return None
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return None
    
    def _generate_openai(
        self,
        token_name: str,
        token_symbol: str,
        description: str,
        style: str,
        output_path: str
    ) -> Optional[str]:
        """Generate using OpenAI DALL-E"""
        try:
            logger.info("Generating with OpenAI DALL-E...")
            
            # Build prompt based on style
            prompt = self._build_prompt(token_name, token_symbol, description, style)
            
            # Call DALL-E API
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1024",
                    "quality": "standard"
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                image_url = data['data'][0]['url']
                
                # Download image
                img_response = requests.get(image_url)
                with open(output_path, 'wb') as f:
                    f.write(img_response.content)
                
                logger.info(f"✅ Generated image with DALL-E: {output_path}")
                return output_path
            else:
                logger.warning(f"DALL-E failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return None
    
    def _generate_stability(
        self,
        token_name: str,
        token_symbol: str,
        description: str,
        style: str,
        output_path: str
    ) -> Optional[str]:
        """Generate using Stability AI"""
        try:
            logger.info("Generating with Stability AI...")
            
            prompt = self._build_prompt(token_name, token_symbol, description, style)
            
            response = requests.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers={
                    "Authorization": f"Bearer {self.stability_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "text_prompts": [{"text": prompt}],
                    "cfg_scale": 7,
                    "height": 1024,
                    "width": 1024,
                    "samples": 1,
                    "steps": 30
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                import base64
                image_data = base64.b64decode(data['artifacts'][0]['base64'])
                
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                
                logger.info(f"✅ Generated image with Stability AI: {output_path}")
                return output_path
            else:
                logger.warning(f"Stability AI failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Stability generation failed: {e}")
            return None
    
    def _generate_local(
        self,
        token_name: str,
        token_symbol: str,
        style: str,
        output_path: str
    ) -> Optional[str]:
        """Generate simple logo locally using PIL"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import random
            
            logger.info("Generating with local PIL...")
            
            # Create 1024x1024 image
            size = 1024
            
            # Choose colors based on style
            if style == "pepe":
                colors = [
                    ("#69C34D", "#FFFFFF"),  # Pepe green + white
                    ("#4CAF50", "#FFFFFF"),
                    ("#8BC34A", "#000000")
                ]
            elif style == "professional":
                colors = [
                    ("#2196F3", "#FFFFFF"),  # Blue
                    ("#673AB7", "#FFFFFF"),  # Purple
                    ("#FF5722", "#FFFFFF")   # Orange
                ]
            else:  # memecoin style
                colors = [
                    ("#FF6B9D", "#FFFFFF"),  # Pink
                    ("#C879FF", "#FFFFFF"),  # Purple
                    ("#00D9FF", "#FFFFFF"),  # Cyan
                    ("#FFD93D", "#000000"),  # Yellow
                    ("#6BCB77", "#FFFFFF")   # Green
                ]
            
            bg_color, text_color = random.choice(colors)
            
            # Create image with gradient background
            img = Image.new('RGB', (size, size), bg_color)
            draw = ImageDraw.Draw(img)
            
            # Draw gradient
            for i in range(size):
                alpha = i / size
                # Simple gradient effect
                brightness = int(255 * (0.7 + 0.3 * alpha))
                color_tuple = tuple(int(bg_color.lstrip('#')[j:j+2], 16) * brightness // 255 
                                   for j in (0, 2, 4))
                draw.line([(0, i), (size, i)], fill=color_tuple)
            
            # Add circular badge
            circle_size = int(size * 0.7)
            circle_pos = (size - circle_size) // 2
            draw.ellipse(
                [circle_pos, circle_pos, circle_pos + circle_size, circle_pos + circle_size],
                fill=bg_color,
                outline=text_color,
                width=10
            )
            
            # Add token symbol text
            try:
                # Try to use a nice font
                font_size = int(size * 0.25)
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                # Fallback to default
                font = ImageFont.load_default()
            
            # Draw frog emoji in center
            frog_emoji = "🐸"
            try:
                # Use larger font for emoji
                emoji_font_size = int(size * 0.35)
                emoji_font = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", emoji_font_size)
            except:
                try:
                    # Fallback to Helvetica with emoji support
                    emoji_font_size = int(size * 0.35)
                    emoji_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", emoji_font_size)
                except:
                    emoji_font = font
            
            # Center the frog emoji
            emoji_bbox = draw.textbbox((0, 0), frog_emoji, font=emoji_font)
            emoji_width = emoji_bbox[2] - emoji_bbox[0]
            emoji_height = emoji_bbox[3] - emoji_bbox[1]
            emoji_x = (size - emoji_width) // 2
            emoji_y = (size - emoji_height) // 2 - int(size * 0.08)  # Slightly above center
            
            draw.text((emoji_x, emoji_y), frog_emoji, font=emoji_font, embedded_color=True)
            
            # Draw "PLOI PEPE" above frog
            ploi_text = "PLOI PEPE"
            try:
                ploi_font_size = int(size * 0.08)  # Smaller branding text
                ploi_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", ploi_font_size)
            except:
                ploi_font = font
            
            ploi_bbox = draw.textbbox((0, 0), ploi_text, font=ploi_font)
            ploi_width = ploi_bbox[2] - ploi_bbox[0]
            ploi_x = (size - ploi_width) // 2
            ploi_y = emoji_y - int(size * 0.15)  # Above the frog
            
            # Draw PLOI PEPE with shadow
            shadow_offset = 3
            draw.text((ploi_x + shadow_offset, ploi_y + shadow_offset), 
                     ploi_text, fill=(0, 0, 0, 128), font=ploi_font)
            draw.text((ploi_x, ploi_y), ploi_text, fill=text_color, font=ploi_font)
            
            # Draw symbol below frog
            symbol_text = token_symbol[:4].upper()  # Max 4 chars
            try:
                symbol_font_size = int(size * 0.15)  # Smaller than before
                symbol_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", symbol_font_size)
            except:
                symbol_font = font
            
            bbox = draw.textbbox((0, 0), symbol_text, font=symbol_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = (size - text_width) // 2
            text_y = emoji_y + emoji_height + int(size * 0.05)  # Below the frog
            
            # Draw text with shadow
            shadow_offset = 4
            draw.text((text_x + shadow_offset, text_y + shadow_offset), 
                     symbol_text, fill=(0, 0, 0, 128), font=symbol_font)
            draw.text((text_x, text_y), symbol_text, fill=text_color, font=symbol_font)
            
            # Add decorative elements for memecoin style
            if style == "memecoin":
                # Add some sparkles/stars
                for _ in range(15):
                    x = random.randint(50, size - 50)
                    y = random.randint(50, size - 50)
                    star_size = random.randint(5, 15)
                    draw.ellipse([x-star_size, y-star_size, x+star_size, y+star_size],
                               fill=text_color)
            
            # Save
            img.save(output_path, 'PNG')
            logger.info(f"✅ Generated local image: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Local generation failed: {e}")
            return None
    
    def _build_prompt(
        self,
        token_name: str,
        token_symbol: str,
        description: str,
        style: str
    ) -> str:
        """Build AI image generation prompt"""
        
        base_prompt = f"Create a cryptocurrency token logo for '{token_name}' (${token_symbol}). "
        
        if style == "pepe":
            base_prompt += "Style: Pepe the frog inspired, meme coin aesthetic, vibrant green colors, fun and casual, crypto theme. Feature a cute frog emoji 🐸 in the center. "
        elif style == "professional":
            base_prompt += "Style: Professional, clean, modern crypto logo, geometric shapes, gradient colors, sleek design. Feature a small frog emoji 🐸 as a subtle mascot. "
        elif style == "memecoin":
            base_prompt += "Style: Fun memecoin aesthetic, vibrant colors, playful, trendy, social media friendly, crypto community vibe. Feature a prominent frog emoji 🐸 in the center as the mascot. "
        else:
            base_prompt += "Style: Modern cryptocurrency logo, clean and recognizable. Include a frog emoji 🐸 in the design. "
        
        if description:
            base_prompt += f"Concept: {description}. "
        
        base_prompt += "IMPORTANT: Include the text 'PLOI PEPE' prominently in the design as branding. 1024x1024px, high quality, circular/badge shape, centered design, bold and eye-catching, frog-themed."
        
        return base_prompt


def generate_token_image(
    token_name: str,
    token_symbol: str,
    description: str = "",
    style: str = "memecoin"
) -> Optional[str]:
    """
    Convenience function to generate token image.
    
    Args:
        token_name: Token name
        token_symbol: Token symbol
        description: Token description
        style: Visual style
    
    Returns:
        Path to generated image
    """
    generator = TokenImageGenerator()
    return generator.generate(token_name, token_symbol, description, style)


if __name__ == "__main__":
    # Test image generation
    print("Testing Token Image Generator...")
    
    print("\nGenerating Pepe token logo...")
    result = generate_token_image(
        token_name="Pepe Coin",
        token_symbol="PEPE",
        description="The OG frog token on Solana",
        style="pepe"
    )
    
    if result:
        print(f"✅ Generated: {result}")
    else:
        print("❌ Generation failed")
