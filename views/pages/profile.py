import streamlit as st

def profile_page():
    """Profile Page with editable fields"""
    st.markdown("### 👤 User Profile")

    # Initialize profile data in session state if not exists
    if 'profile_data' not in st.session_state:
        st.session_state.profile_data = {
            "username": "user_123",
            "display_name": "StoryLover",
            "bio": "I love chatting with AI characters!",
            "avatar": "🧙",
            "theme": "system",
            "created_at": "2024-01-01"
        }

    # Avatar selection
    st.write("**Choose Avatar:**")
    avatar_cols = st.columns(5)
    avatars = ['👤', '👨', '👩', '🧙', '🦸']
    for i, avatar in enumerate(avatars):
        with avatar_cols[i]:
            if st.button(avatar, key=f"avatar_{i}"):
                st.session_state.profile_data["avatar"] = avatar
                st.toast(f"Avatar changed to {avatar}!", icon="👍")

    st.divider()

    # Editable fields form
    with st.form(key="profile_form"):
        # Form fields implementation...
        pass

    # Current avatar preview
    st.markdown("### Your Profile Preview")
    with st.container(border=True):
        cols = st.columns([1, 3])
        with cols[0]:
            st.markdown(
                f"<div style='font-size: 3rem; text-align: center;'>{st.session_state.profile_data['avatar']}</div>",
                unsafe_allow_html=True
            )
        with cols[1]:
            st.markdown(f"**{st.session_state.profile_data['display_name']}**")
            st.write(st.session_state.profile_data['bio'])

    # Back button
    if st.button("🔙 Back to Home"):
        st.session_state.page = "home"
        st.rerun()