import streamlit as st
import io
import base64
from PIL import Image
from dotenv import load_dotenv
import os
from groq import Groq
import csv
import tempfile

# --- ENVIRONMENT SETUP ---
load_dotenv()
def get_env_api_key():
    return os.environ.get('GROQ_API_KEY')

# --- GROQ API HELPERS ---
def extract_detailed_description(image, api_key, model):
    try:
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        image_bytes = buffered.getvalue()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        client = Groq(api_key=api_key)
        prompt = (
            "You are an expert at identifying items for online resale. "
            "Carefully analyze the image and reason step-by-step about what each distinct, complete, and sellable item is. "
            "For each object, consider its shape, color, size, visible logos, text, context, and any clues from the scene. "
            "Infer likely category, brand, model, and condition if possible. "
            "If multiple items are similar, group them as a set (e.g., 'set of 4 matching dinner plates'). "
            "Ignore background, packaging, or partial/fragmented objects. "
            "If you are unsure, explain your reasoning and make your best guess. "
            "Return a numbered list, one item per line, with a short, clear description for each (e.g., '1. Nike Air Max sneakers, men's size 10, gently used'). "
            "If you cannot confidently identify an item, state what you see and your reasoning."
        )
        chat_completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }],
            model=model
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error extracting description: {e}"

def generate_listing_details_llm(item_list, context, api_key, model, custom_prompt=None):
    try:
        if not model:
            return "Error: No valid model selected."
        client = Groq(api_key=api_key)
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = (
                "You are a professional online seller. Given the following detailed image description and a list of items to sell, generate a catchy, creative, and highly marketable title, a vivid and persuasive description that highlights unique features and benefits, and a realistic suggested price in USD (based on typical secondhand/marketplace value, not new retail). "
                "Make the listing sound exciting and appealing to buyers. Use strong, positive language and avoid repetition. "
                "Return the results as a markdown table with columns: Item, Title, Description, Suggested Price.\n\nImage description: " + context + "\n\nList: " + item_list
            )
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error generating listing details: {e}"

def markdown_table_to_csv(md_table):
    lines = [line for line in md_table.split('\n') if '|' in line and not line.strip().startswith('|---')]
    if not lines or len(lines) < 2:
        return ''
    headers = [h.strip() for h in lines[0].split('|')[1:-1]]
    rows = [[c.strip() for c in row.split('|')[1:-1]] for row in lines[1:]]
    with tempfile.NamedTemporaryFile(delete=False, mode='w+', newline='', suffix='.csv') as tmp:
        writer = csv.writer(tmp)
        writer.writerow(headers)
        writer.writerows(rows)
        tmp.seek(0)
        return tmp.read()

# --- SIDEBAR SETTINGS ---
st.sidebar.title("ListGenie Settings")
if 'user_api_key' not in st.session_state:
    st.session_state['user_api_key'] = ''
user_api_key = st.sidebar.text_input("Enter your Groq API key", value=st.session_state['user_api_key'], type="password")
if user_api_key:
    st.session_state['user_api_key'] = user_api_key
endpoint = st.sidebar.selectbox("Choose endpoint", ["chat.completions", "other (manual)"])
# Model selection (populated after API key entry)
model_list = []
model_error = None
if user_api_key:
    try:
        client = Groq(api_key=user_api_key)
        models = client.models.list()
        model_list = [m.id for m in models.data]
    except Exception as e:
        model_error = str(e)
# Vision model selection
vision_models = [m for m in model_list if 'scout' in m.lower() or 'maverick' in m.lower() or 'llava' in m.lower() or 'vision' in m.lower()]
if vision_models:
    selected_vision_model = st.sidebar.selectbox("Choose vision model (for image analysis)", vision_models)
else:
    selected_vision_model = None
    if model_error:
        st.sidebar.error(f"Model fetch error: {model_error}")
# LLM model selection (for listing generation)
# Force compound-beta for LLM step
selected_llm_model = 'mixtral-8x7b-32768'  # fallback if compound-beta not found
for m in model_list:
    if 'compound-beta' in m.lower():
        selected_llm_model = m
        break

# Gray out non-vision models in the selectbox
import streamlit.components.v1 as components
if model_list:
    custom_css = """
    <style>
    .stSelectbox [data-baseweb="select"] [aria-selected="true"] {
        color: #000 !important;
    }
    .stSelectbox [data-baseweb="select"] [aria-selected="false"] {
        color: #888 !important;
    }
    </style>
    """
    components.html(custom_css, height=0)
active_api_key = user_api_key if user_api_key else get_env_api_key()
active_vision_model = selected_vision_model
active_llm_model = selected_llm_model
active_endpoint = endpoint

# --- MAIN APP LOGIC ---
def main():
    st.title("ListGenie: Effortless Selling Post Generator")
    st.markdown("""
    <div style='background-color:#f0f2f6;padding:1em;border-radius:10px;margin-bottom:1em;'>
    <b>Welcome to ListGenie!</b><br>
    <ul>
      <li><b>Step 1:</b> <span style='color:#1a73e8'>Upload a photo</span> of your items (just drag & drop or click the upload box).</li>
      <li><b>Step 2:</b> <span style='color:#1a73e8'>Select what you're selling</span> from the list ListGenie finds in your photo.</li>
      <li><b>Step 3:</b> <span style='color:#1a73e8'>Generate your listing</span> with one click!</li>
      <li><b>Step 4:</b> <span style='color:#1a73e8'>Chat with ListGenie</span> any time if you have questions or want to fix something.</li>
    </ul>
    <b>Tip:</b> You don't need any tech skills. If you get stuck, just ask in the chat below!
    </div>
    """, unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload an item image", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        if 'items' not in st.session_state or st.button("Process Image"):
            if not active_vision_model:
                st.error("No vision-capable model is available. Please check your API key or Groq account.")
                return
            st.write("Processing the image with AI...")
            result = extract_detailed_description(image, active_api_key, model=active_vision_model)
            st.session_state['raw_result'] = result
            # Robust error handling for None, empty, or error results
            if not result or not isinstance(result, str) or result.strip() == '' or result.lower().startswith("error"):
                st.error("No items detected or an error occurred. Please try another image or check your model/API key.")
                st.session_state.pop('items', None)
                st.session_state.pop('selected_items', None)
                st.session_state.pop('background_items', None)
                st.session_state.pop('listing_md', None)
                st.session_state.pop('post_text', None)
                st.session_state.pop('detailed_desc', None)
                return
            items = [line.strip('- ').strip() for line in result.split('\n') if line.strip() and not line.lower().startswith('error')]
            if not items:
                st.error("No items detected in the image. Please try another image.")
                st.session_state.pop('items', None)
                st.session_state.pop('selected_items', None)
                st.session_state.pop('background_items', None)
                st.session_state.pop('listing_md', None)
                st.session_state.pop('post_text', None)
                st.session_state.pop('detailed_desc', None)
                return
            st.session_state['items'] = items
            st.session_state['selected_items'] = items
            st.session_state['background_items'] = []
            st.session_state['listing_md'] = None
            st.session_state['post_text'] = None
            st.session_state['detailed_desc'] = result
        # Item selection UI
        if 'items' in st.session_state:
            items = st.session_state['items']
            selected_items = st.multiselect(
                "Select the items you are selling (unselected will be treated as background):",
                items,
                default=st.session_state.get('selected_items', items)
            )
            st.session_state['selected_items'] = selected_items
            background_items = [item for item in items if item not in selected_items]
            st.session_state['background_items'] = background_items
            st.write("**Selling:**", selected_items)
            st.write("**Background/Not for sale:**", background_items)
            # Show button to generate listing only if at least one item is selected
            if selected_items and active_llm_model:
                if st.button("Generate Listing Details (LLM)"):
                    with st.spinner("Generating listing details with LLM..."):
                        prompt_items = "\n".join(selected_items)
                        # Enhanced prompt for compound-beta with web search, pricing, and image reasoning
                        compound_prompt = (
                            "You are a professional online seller and expert product researcher. Given the following detailed image description and a list of items to sell, do the following for each item: "
                            "1. Carefully reason about the image description to clarify what each item is, its likely condition, and any unique or notable features.\n"
                            "2. Use web search and your knowledge to determine the most accurate and up-to-date secondhand/marketplace value for each item (not new retail).\n"
                            "3. Generate a catchy, creative, and highly marketable title.\n"
                            "4. Write a vivid, persuasive description that highlights unique features, benefits, and likely buyer interests.\n"
                            "5. Suggest a realistic price in USD, based on your research.\n"
                            "6. If possible, include a short bullet list of selling points.\n"
                            "Return the results as a markdown table with columns: Item, Title, Description, Suggested Price, Selling Points.\n"
                            "If you need to clarify what the item is, use the detailed image description below.\n"
                            "You may use web search, recent pricing data, and your own knowledge.\n"
                            f"\nImage description: {st.session_state['detailed_desc']}\n\nList: {prompt_items}"
                        )
                        listing_md = generate_listing_details_llm(prompt_items, st.session_state['detailed_desc'], active_api_key, model=active_llm_model, custom_prompt=compound_prompt)
                        st.session_state['listing_md'] = listing_md
                        st.session_state['post_text'] = None
            # Show listing details and post template only after generation
            if st.session_state.get('listing_md') and active_llm_model:
                st.subheader("Listing Details (AI Generated)")
                st.markdown(st.session_state['listing_md'], unsafe_allow_html=True)
                csv_data = markdown_table_to_csv(st.session_state['listing_md'])
                if csv_data:
                    st.download_button("Download as CSV", data=csv_data, file_name="listing.csv")
                st.button("Copy Listing Text", on_click=lambda: st.session_state.update({'copied': True}))
                if st.session_state.get('copied'):
                    st.success("Listing text copied to clipboard! (Use your system copy)")
                # Social/marketplace post template
                st.subheader("Marketplace Post Template")
                post_text = f"Selling these items!\n\n{', '.join(st.session_state['selected_items'])}\n\nDM for details and prices!"
                if not st.session_state.get('post_text'):
                    st.session_state['post_text'] = post_text
                st.write(st.session_state['post_text'])
                st.markdown("---")
                st.write("**Enhance your post:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Make it more persuasive") and active_llm_model:
                        prompt = f"Rewrite this selling post to be more persuasive and engaging:\n\n{st.session_state['post_text']}"
                        client = Groq(api_key=active_api_key)
                        chat_completion = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model=active_llm_model
                        )
                        st.session_state['post_text'] = chat_completion.choices[0].message.content
                with col2:
                    if st.button("Add urgency") and active_llm_model:
                        prompt = f"Rewrite this selling post to add urgency and encourage quick action:\n\n{st.session_state['post_text']}"
                        client = Groq(api_key=active_api_key)
                        chat_completion = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model=active_llm_model
                        )
                        st.session_state['post_text'] = chat_completion.choices[0].message.content
                with col3:
                    if st.button("Make it concise") and active_llm_model:
                        prompt = f"Rewrite this selling post to be concise and to the point:\n\n{st.session_state['post_text']}"
                        client = Groq(api_key=active_api_key)
                        chat_completion = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model=active_llm_model
                        )
                        st.session_state['post_text'] = chat_completion.choices[0].message.content
                st.write(st.session_state['post_text'])
            # --- Optional Chat with Model for Corrections (now available before listing generation) ---
            st.markdown("---")
            st.subheader("Chat with the Model (Optional)")
            st.write("You can chat with the model at any time to clarify, correct, or ask questions about your items, the image, or the listing process.")
            chat_container = st.container()
            if 'chat_history' not in st.session_state:
                st.session_state['chat_history'] = []
            clear_col, _ = st.columns([1, 5])
            with clear_col:
                if st.button("Clear Chat"):
                    st.session_state['chat_history'] = []
                    st.experimental_set_query_params(dummy=str(len(st.session_state['chat_history'])))
            for msg in st.session_state['chat_history']:
                if hasattr(st, 'chat_message'):
                    with st.chat_message("user" if msg['role'] == 'user' else "assistant"):
                        st.markdown(msg['content'])
                else:
                    if msg['role'] == 'user':
                        st.markdown(f"**🧑 You:** {msg['content']}")
                    else:
                        st.markdown(f"**🤖 Model:** {msg['content']}")
            user_chat_input = st.text_area("Ask a question about your image, items, or the listing process", key="chat_input")
            send_col, regen_col = st.columns([1, 1])
            send_clicked = send_col.button("Send", key="chat_send")
            regen_clicked = regen_col.button("Regenerate Last", key="regen_btn")
            # Chat send logic
            if send_clicked and user_chat_input:
                # Use available context: image description, items, or a default system prompt
                if st.session_state.get('listing_md'):
                    initial_context = f"Here is the current listing markdown table:\n\n{st.session_state['listing_md']}\n\n"
                elif st.session_state.get('detailed_desc'):
                    initial_context = f"Here is the detailed image description:\n\n{st.session_state['detailed_desc']}\n\n"
                else:
                    initial_context = "You are a helpful assistant for online sellers. Answer questions about item identification, listing creation, and selling tips."
                chat_messages = st.session_state['chat_history'] + [
                    {"role": "user", "content": user_chat_input}
                ]
                client = Groq(api_key=active_api_key)
                messages = [{"role": "system", "content": initial_context}] + chat_messages
                with chat_container:
                    with st.spinner("Model is thinking..."):
                        try:
                            chat_completion = client.chat.completions.create(
                                messages=messages,
                                model=active_llm_model
                            )
                            model_reply = chat_completion.choices[0].message.content
                        except Exception as e:
                            model_reply = f"Error: {e}"
                st.session_state['chat_history'].append({"role": "user", "content": user_chat_input})
                st.session_state['chat_history'].append({"role": "assistant", "content": model_reply})
                st.experimental_set_query_params(dummy=str(len(st.session_state['chat_history'])))
            # Regenerate last model reply
            if regen_clicked and st.session_state['chat_history']:
                if st.session_state['chat_history'][-1]['role'] == 'assistant':
                    st.session_state['chat_history'].pop()
                if st.session_state['chat_history'] and st.session_state['chat_history'][-1]['role'] == 'user':
                    last_user_msg = st.session_state['chat_history'][-1]['content']
                    chat_messages = st.session_state['chat_history']
                    if st.session_state.get('listing_md'):
                        initial_context = f"Here is the current listing markdown table:\n\n{st.session_state['listing_md']}\n\n"
                    elif st.session_state.get('detailed_desc'):
                        initial_context = f"Here is the detailed image description:\n\n{st.session_state['detailed_desc']}\n\n"
                    else:
                        initial_context = "You are a helpful assistant for online sellers. Answer questions about item identification, listing creation, and selling tips."
                    client = Groq(api_key=active_api_key)
                    messages = [{"role": "system", "content": initial_context}] + chat_messages
                    with chat_container:
                        with st.spinner("Model is thinking..."):
                            try:
                                chat_completion = client.chat.completions.create(
                                    messages=messages,
                                    model=active_llm_model
                                )
                                model_reply = chat_completion.choices[0].message.content
                            except Exception as e:
                                model_reply = f"Error: {e}"
                    st.session_state['chat_history'].append({"role": "assistant", "content": model_reply})
                    st.experimental_set_query_params(dummy=str(len(st.session_state['chat_history'])))
    # Show API key status safely
    if active_api_key:
        st.info(f"Loaded API key: {active_api_key[:4]}...{active_api_key[-4:]}")
    else:
        st.info("No API key loaded.")

if __name__ == "__main__":
    main()
