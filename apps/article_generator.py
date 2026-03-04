import streamlit as st
import os
import json
import requests
import base64
import pandas as pd
import markdown
import re
from openai import OpenAI
from dotenv import load_dotenv

# --- LOAD ENV ---
load_dotenv()

# --- PAGE CONFIG ---
st.set_page_config(page_title="OpenSEO Restore", layout="wide", page_icon="⚡")

# --- SESSION STATE ---
if "generated_plan" not in st.session_state: st.session_state.generated_plan = None
if "config" not in st.session_state: st.session_state.config = {}

# --- SIDEBAR: CREDENTIALS ---
with st.sidebar:
    has_env_keys = os.getenv("OPENAI_API_KEY") is not None
    expand_creds = not has_env_keys
    status_icon = "✅" if has_env_keys else "⚠️"
    
    with st.expander(f"{status_icon} Credentials", expanded=expand_creds):
        api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        st.divider()
        wp_url = st.text_input("WP Base URL", value=os.getenv("WP_BASE_URL", ""))
        wp_user = st.text_input("WP Username", value=os.getenv("WP_USERNAME", ""))
        wp_pass = st.text_input("WP App Password", type="password", value=os.getenv("WP_APP_PASSWORD", ""))
        st.divider()
        wp_status = st.selectbox("Post Status", ["draft", "publish"], index=0)

# --- HELPER FUNCTIONS ---

def get_size_instructions(size_selection):
    if "Short" in size_selection:
        return "Strictly limit to 3-4 H2 subheadings. Under each H2, use exactly 2 H3 subheadings. Target ~800 words."
    elif "Standard" in size_selection:
        return "Create 5-8 H2 subheadings. Under each H2, YOU MUST include 3-4 H3 subheadings. Target ~1,500 words."
    elif "Long-Form" in size_selection:
        return "Create 9-12 H2 subheadings. Under each H2, include at least 4 H3 subheadings. Target ~2,500 words."
    return "Standard structure."

def generate_dalle_image(client, prompt, style, size):
    try:
        full_prompt = f"{style} style. {prompt}"
        response = client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size=size,
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        return None

def upload_image_to_wp(img_url, title):
    img_data = requests.get(img_url).content
    filename = f"{title.replace(' ', '-').lower()}.png"
    credentials = f"{wp_user}:{wp_pass}"
    token = base64.b64encode(credentials.encode())
    headers = {
        'Authorization': f'Basic {token.decode("utf-8")}',
        'Content-Type': 'image/png',
        'Content-Disposition': f'attachment; filename={filename}'
    }
    api_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/media"
    try:
        res = requests.post(api_url, headers=headers, data=img_data)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return None

# --- AI FUNCTIONS ---

def generate_plan(seed, config):
    client = OpenAI(api_key=api_key)
    
    # STEP 1: TOPICS
    batch_limit = config['batch_size']
    topic_prompt = f"""
    Role: Expert SEO Strategist.
    Task: Create a content calendar for Seed Keyword: "{seed}".
    Target Country: {config['country']}.
    
    RULES:
    1. Generate EXACTLY {batch_limit} unique topics.
    2. Titles: Click-worthy, 6-9 words. NO COLONS.
    
    Output JSON: {{ "topics": [ {{ "keyword": "...", "title": "..." }} ] }}
    """
    
    try:
        res_topics = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": topic_prompt}],
            response_format={"type": "json_object"}
        )
        topics = json.loads(res_topics.choices[0].message.content).get('topics', [])
    except Exception as e:
        st.error(f"Topic Gen Error: {e}")
        return []

    # STEP 2: OUTLINES (LOOP)
    final_plan = []
    size_instr = get_size_instructions(config['size'])
    
    plan_bar = st.progress(0)
    
    for idx, topic in enumerate(topics):
        outline_prompt = f"""
        You are an SEO Architect.
        Create a detailed content brief for:
        Title: "{topic['title']}"
        Keyword: "{topic['keyword']}"
        
        CONSTRAINTS:
        1. {size_instr}
        2. Readability: {config['readability']}
        3. OUTLINE: Markdown headers only (H2, H3). No descriptions.
        
        TASK:
        1. Generate 5 distinct NLP/LSI keywords specific to this topic.
        2. Create the Outline.
        
        Output JSON: {{ "nlp_keywords": "...", "outline": "..." }}
        """
        
        try:
            res_outline = client.chat.completions.create(
                model="gpt-5-nano",
                messages=[{"role": "user", "content": outline_prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(res_outline.choices[0].message.content)
            
            final_plan.append({
                "selected": True,
                "keyword": topic['keyword'],
                "title": topic['title'],
                "nlp_keywords": data.get('nlp_keywords', ''),
                "outline": data.get('outline', '')
            })
        except Exception as e:
            pass
        
        plan_bar.progress((idx + 1) / len(topics))

    plan_bar.empty()
    return final_plan

def write_article(post_data, config):
    client = OpenAI(api_key=api_key)
    
    # Logic to enable/disable images in the prompt
    image_instr = "Insert Ghost Image placeholders: [IMAGE_PROMPT: visual description]."
    if not config['media']['enabled']:
        image_instr = "DO NOT insert image placeholders."

    # Logic to enable/disable specific sections
    takeaway_instr = "Immediately after the intro, insert a 'Key Takeaways' bullet list."
    if not config['structure']['Key Takeaways']:
        takeaway_instr = "Do NOT include a Key Takeaways section."
        
    faq_instr = "End with a 'Frequently Asked Questions' section."
    if not config['structure']['FAQ']:
        faq_instr = "Do NOT include an FAQ section."

    # The XML System Prompt
    prompt = f"""
    <System_Prompt>

    <Role_and_Objectives>
        <Role>World-Class SEO Content Writer</Role>
        <Mission>
            To generate content that is indistinguishable from human authorship. You possess the expertise to capture emotional nuance, cultural relevance, and contextual authenticity.
        </Mission>
        <Objective>
            Produce a high-performance article based on the provided Title and Outline.
            Target Audience Locale: {config['country']}
            Language: {config['language']}
        </Objective>
    </Role_and_Objectives>

    <Instructions>
        <Architectural_Blueprint>
            You must adhere to this strict Markdown structure:

            <Element_1 type="Hook">
                Start immediately with a high-voltage Hook (Statistic, Quote, or Question).
                Formatting: Use Markdown italics (*text*) for the entire hook.
                Constraint: Do not use a single weak sentence. The hook must be 2-3 sentences that disrupt the reader's assumptions.
            </Element_1>

            <Element_2 type="Intro">
                Follow the hook with a concise, punchy introduction.
            </Element_2>

            <Element_3 type="Takeaways">
                {takeaway_instr}
            </Element_3>

            <Element_4 type="Body">
                Use strict Markdown hierarchy (## for Main Sections, ### for Sub-sections).
                CRITICAL RULE: "No Orphan Headers." You MUST write a transition paragraph under every ## H2 before diving into the ### H3s.
            </Element_4>

            <Element_5 type="Images">
                {image_instr}
            </Element_5>

            <Element_6 type="FAQ">
                {faq_instr}
            </Element_6>
        </Architectural_Blueprint>

        <Style_Enforcement>
            <Tone_and_Voice>
                1. **Selected Tone:** {config['tone']}
                2. **Point of View:** {config['pov']}
                3. **Conversational:** Use contractions, idioms, and colloquialisms ("You know what?", "Honestly").
                4. **Burstiness:** Mix short, impactful sentences (1-3 words) with longer, complex ones.
            </Tone_and_Voice>

            <Banned_List>
                DO NOT USE: opt, dive, unlock, unleash, intricate, utilization, transformative, alignment, proactive, scalable, benchmark.
                DO NOT USE: "In this world," "in today's world," "at the end of the day," "in order to," "best practices".
            </Banned_List>

            <Formatting_Rules>
                1. **Paragraphs:** Mix lengths drastically.
                2. **No Lists in Body:** Inside H3 sections, write full paragraphs. Avoid bullet points unless presenting data.
                3. **No Meta-Commentary:** Do not say "Here is the article." Just write.
            </Formatting_Rules>
        </Style_Enforcement>
    </Instructions>

    <Initialization>
        TASK: Write article for Title: "{post_data['title']}"
        OUTLINE TO FOLLOW: {post_data['outline']}
    </Initialization>

    </System_Prompt>
    """
    
    res = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content

# --- UI DASHBOARD ---

st.title("⚡ OpenSEO Restore")

# 1. GLOBAL SETTINGS
with st.container(border=True):
    c_seed, c_batch = st.columns([3, 1])
    with c_seed: 
        seed_input = st.text_input("Enter Seed Keyword", placeholder="e.g., Urban Gardening")
    with c_batch:
        batch_size = st.number_input("Batch Size", min_value=1, max_value=5, value=3, help="Limit 1-5.")

    st.divider()
    
    c1, c2, c3 = st.columns(3)
    with c1: language = st.selectbox("Language", ["English (US)", "English (UK)", "Spanish", "French", "German"])
    with c2: country = st.selectbox("Target Country", ["United States", "United Kingdom", "Global"])
    with c3: art_type = st.selectbox("Article Type", ["Standard Informational", "How-to Guide", "Listicle", "Product Review"])
    
    c4, c5, c6 = st.columns(3)
    with c4: size = st.selectbox("Size", ["Standard (1000-2000w)", "Short (600-1000w)", "Long-Form (2000w+)"])
    with c5: tone = st.selectbox("Tone", ["Professional", "Conversational", "Witty", "Authoritative"])
    with c6: pov = st.selectbox("POV", ["Second Person (You)", "First Person Singular (I)", "First Person Plural (We)", "Third Person (They/It)"])

# 2. MEDIA ENGINE
with st.container(border=True):
    st.markdown("#### 🎨 Media")
    use_images = st.toggle("Generate AI Images?", value=False)
    if use_images:
        c_img1, c_img2, c_img3 = st.columns(3)
        with c_img1: img_count = st.number_input("Count", min_value=1, max_value=5, value=1)
        with c_img2: img_style = st.selectbox("Style", ["Photo", "Cyberpunk", "Cinematic", "Cartoon", "Abstract"])
        with c_img3: img_size = st.selectbox("Size", ["1024x1024", "1024x1792 (Portrait)", "1792x1024 (Landscape)"])
    else:
        img_count, img_style, img_size = 0, "None", "1024x1024"

# --- GENERATE PLAN ---
if st.button("GENERATE PLAN 🎯", type="primary"):
    if not api_key:
        st.error("Missing API Key")
    else:
        # We add 'structure' back in, hardcoded to True
        config = {
            "language": language, 
            "country": country, 
            "type": art_type, 
            "size": size, 
            "tone": tone, 
            "readability": "Standard",
            "pov": pov, 
            "batch_size": batch_size,
            
            # --- THE FIX: Hardcode the structure keys ---
            "structure": {"Key Takeaways": True, "FAQ": True},
            
            "media": {"enabled": use_images, "count": img_count, "style": img_style, "size": img_size}
        }
        
        with st.spinner("Architecting Content Plan..."):
            st.session_state.config = config
            st.session_state.generated_plan = generate_plan(seed_input, config)
            st.rerun()

# --- EXECUTION ---
if st.session_state.generated_plan:
    st.divider()
    st.markdown("### Review & Launch")
    
    df = pd.DataFrame(st.session_state.generated_plan)
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", hide_index=True)
    
    if st.button("🚀 LAUNCH PRODUCTION"):
        final_plan = edited_df.to_dict(orient="records")
        to_process = [p for p in final_plan if p.get('selected', True)]
        
        client = OpenAI(api_key=api_key)
        bar = st.progress(0)
        log = st.empty()
        
        results = []
        
        for i, post in enumerate(to_process):
            log.text(f"Writing: {post['title']}...")
            
            # 1. Generate Text
            raw_text = write_article(post, st.session_state.config)
            final_html = raw_text
            featured_media_id = 0
            
            # 2. Handle Images
            if st.session_state.config['media']['enabled']:
                img_prompts = re.findall(r'\[IMAGE_PROMPT:\s*(.*?)\]', raw_text)
                
                for idx, prompt in enumerate(img_prompts):
                    log.text(f"🎨 Image {idx+1}...")
                    dalle_url = generate_dalle_image(client, prompt, st.session_state.config['media']['style'], st.session_state.config['media']['size'])
                    
                    if dalle_url and wp_url:
                        wp_img = upload_image_to_wp(dalle_url, f"{post['keyword']} {idx}")
                        if wp_img:
                            if idx == 0:
                                # FIRST IMAGE: Featured only (Hidden from body)
                                featured_media_id = wp_img['id']
                                final_html = final_html.replace(f"[IMAGE_PROMPT: {prompt}]", "")
                            else:
                                # OTHERS: Embedded
                                img_tag = f'<img src="{wp_img["source_url"]}" alt="{prompt}" class="wp-image-{wp_img["id"]}" />'
                                final_html = final_html.replace(f"[IMAGE_PROMPT: {prompt}]", img_tag)
            
            # 3. Cleanup
            final_html = re.sub(r'\[IMAGE_PROMPT:.*?\]', '', final_html)
            
            # 4. Post
            # Explicitly enable extensions to catch tables/lists if they exist
            html_body = markdown.markdown(final_html, extensions=['tables', 'fenced_code'])
            
            if wp_url:
                credentials = f"{wp_user}:{wp_pass}"
                token = base64.b64encode(credentials.encode())
                headers = {'Authorization': f'Basic {token.decode("utf-8")}'}
                payload = {
                    'title': post['title'], 'content': html_body, 
                    'status': wp_status, 'slug': post['keyword'].replace(" ", "-").lower(),
                    'featured_media': featured_media_id
                }
                try:
                    r = requests.post(f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts", headers=headers, json=payload)
                    results.append({"Title": post['title'], "Status": "✅ Posted", "Link": r.json().get('link')})
                except Exception as e:
                    results.append({"Title": post['title'], "Status": "❌ Error", "Link": str(e)})
            
            bar.progress((i + 1) / len(to_process))
            
        st.success("Batch Complete!")
        st.dataframe(results)