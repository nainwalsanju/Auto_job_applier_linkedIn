"""
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html

GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

version:    25.01.15.01.00
"""

###################################################### CONFIGURE YOUR TOOLS HERE ######################################################

# ⚠️  WARNING: Credentials are now loaded from environment variables or .env file!
# See .env.example for the list of environment variables.
# For security reasons, do NOT hardcode credentials in this file.

# Legacy support: These variables are kept for backward compatibility.
# They are now loaded from secure_config.py which reads from environment variables.

# DO NOT EDIT THESE VALUES HERE - THEY ARE LOADED FROM ENVIRONMENT
# Use a .env file or set environment variables instead.

# LinkedIn Credentials - Use LINKEDIN_USERNAME and LINKEDIN_PASSWORD environment variables
# Example: export LINKEDIN_USERNAME="your_email@example.com"
#          export LINKEDIN_PASSWORD="your_password"

# AI Configuration - Use environment variables:
# USE_AI=true/false
# AI_PROVIDER=openai/deepseek/gemini
# LLM_API_URL=https://api...
# LLM_API_KEY=your-api-key
# LLM_MODEL=model-name
# LLM_SPEC=openai/openai-like
# STREAM_OUTPUT=true/false

# Get credentials from secure configuration (environment variables)
from config.secure_config import (
    get_linkedin_username,
    get_linkedin_password,
    get_ai_config,
    use_ai,
    get_ai_provider,
    get_llm_api_key,
)

# Backward compatibility - these will load from environment
username = get_linkedin_username()
password = get_linkedin_password()
use_AI = use_ai()
ai_provider = get_ai_provider()

# AI Configuration - loaded from secure_config (environment variables)
ai_config = get_ai_config()

# For backward compatibility with existing code
llm_api_url = ai_config.llm_api_url
llm_api_key = get_llm_api_key()
llm_model = ai_config.llm_model
llm_spec = ai_config.llm_spec
stream_output = ai_config.stream_output

# ============================================================================
# DEPRECATION NOTICE
# ============================================================================
# The following variables are DEPRECATED and will be removed in a future version.
# Please migrate to using config.secure_config or environment variables.
#
# Old usage:
#   from config.secrets import username, password, llm_api_key
#
# New usage:
#   from config.secure_config import get_linkedin_credentials, get_llm_api_key
#   username, password = get_linkedin_credentials()
#   api_key = get_llm_api_key()
# ============================================================================

############################################################################################################
"""
THANK YOU for using my tool 😊! Wishing you the best in your job hunt 🙌🏻!

Sharing is caring! If you found this tool helpful, please share it with your peers 🥺. Your support keeps this project alive.

Support my work on <PATREON_LINK>. Together, we can help more job seekers.

As an independent developer, I pour my heart and soul into creating tools like this, driven by the genuine desire to make a positive impact.

Your support, whether through donations big or small or simply spreading the word, means the world to me and helps keep this project alive and thriving.

Gratefully yours 🙏🏻,
Sai Vignesh Golla
"""
############################################################################################################
