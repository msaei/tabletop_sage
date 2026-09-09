"""
Capstone Frontend — Streamlit UI
==============================================
Interactive web interface for Tabletop Sage:
- 🔍 Game Bank: Search, browse, and save board games to personal library
- 📚 My Library: View curated collection and quick-launch game workspaces
- ⚔️ Game Workspace: Side-by-side / Tabbed official rulebook reader & RAG rules referee
- 📤 Upload Portal: Contribute new board games and rulebooks to the bank
"""

import uuid

import api_client
import streamlit as st

# ─── Page Configuration & Custom Styling ──────────────────────────────────────

st.set_page_config(
    page_title="Tabletop Sage — Board Game Referee",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern UI cards, badges, and citations
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }
    .game-card {
        border-radius: 12px;
        padding: 1.25rem;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 1rem;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .game-card:hover {
        border-color: #6366f1;
        transform: translateY(-2px);
    }
    .badge-confidence-high {
        background-color: #065f46;
        color: #6ee7b7;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-confidence-med {
        background-color: #78350f;
        color: #fde68a;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-confidence-low {
        background-color: #7f1d1d;
        color: #fca5a5;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .meta-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        color: #e2e8f0;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 6px;
        margin-bottom: 5px;
    }
    .meta-category {
        background: rgba(99, 102, 241, 0.18);
        border-color: rgba(99, 102, 241, 0.4);
        color: #c7d2fe;
    }
    .meta-complexity {
        background: rgba(168, 85, 247, 0.18);
        border-color: rgba(168, 85, 247, 0.4);
        color: #e9d5ff;
    }
    .meta-publisher {
        background: rgba(14, 165, 233, 0.15);
        border-color: rgba(14, 165, 233, 0.35);
        color: #bae6fd;
    }
    .citation-box {
        background: rgba(99, 102, 241, 0.08);
        border-left: 3px solid #6366f1;
        padding: 0.75rem;
        border-radius: 4px;
        margin-top: 0.5rem;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_game_metadata_badges(game: dict):
    """Renders visual pill badges for game specifics (player count, age, playtime, category, complexity, publisher)."""
    badges = []

    # Player count (min, max, or exact)
    min_p = game.get("min_players")
    max_p = game.get("max_players")
    if min_p and max_p:
        if min_p == max_p:
            badges.append(f'<span class="meta-badge">👥 {min_p} Players</span>')
        else:
            badges.append(f'<span class="meta-badge">👥 {min_p}–{max_p} Players</span>')
    elif min_p:
        badges.append(f'<span class="meta-badge">👥 {min_p}+ Players</span>')
    elif max_p:
        badges.append(f'<span class="meta-badge">👥 Up to {max_p} Players</span>')

    # Minimum age
    min_age = game.get("min_age")
    if min_age:
        badges.append(f'<span class="meta-badge">🎂 Age {min_age}+</span>')

    # Estimated playtime
    playtime = game.get("estimated_playtime")
    if playtime:
        badges.append(f'<span class="meta-badge">⏱️ {playtime} min</span>')

    # Category / Genre
    category = game.get("category")
    if category:
        badges.append(f'<span class="meta-badge meta-category">🧩 {category}</span>')

    # Complexity
    complexity = game.get("complexity")
    if complexity:
        badges.append(f'<span class="meta-badge meta-complexity">⚖️ {complexity}</span>')

    # Publisher & Year
    pub = game.get("publisher")
    yr = game.get("year_published")
    if pub and yr:
        badges.append(f'<span class="meta-badge meta-publisher">🏢 {pub} ({yr})</span>')
    elif pub:
        badges.append(f'<span class="meta-badge meta-publisher">🏢 {pub}</span>')
    elif yr:
        badges.append(f'<span class="meta-badge">📅 {yr}</span>')

    if badges:
        st.markdown(f'<div style="margin: 0.4rem 0 0.5rem 0;">{" ".join(badges)}</div>', unsafe_allow_html=True)

# ─── Session State Initialization ─────────────────────────────────────────────

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "selected_game_id" not in st.session_state:
    st.session_state.selected_game_id = None
if "selected_game_name" not in st.session_state:
    st.session_state.selected_game_name = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}  # Dict: game_id -> list of message dicts
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "🔍 Game Bank"


# ─── Sidebar: Branding, Health, Auth, Navigation ──────────────────────────────

with st.sidebar:
    st.markdown("### 🎲 **Tabletop Sage**")
    st.caption("RAG-Powered Rules Referee & Game Library")

    # Backend Health Check indicator
    health = api_client.get_health()
    if health.get("status") == "ok":
        st.success("● Backend & Vector DB Online", icon="🟢")
    elif health.get("status") == "degraded":
        st.warning("▲ Backend Online (LLM / Chroma degraded)", icon="🟡")
    else:
        st.error("✕ Backend Offline", icon="🔴")

    st.markdown("---")

    # User Authentication Card
    if st.session_state.token and st.session_state.user:
        st.markdown(f"👤 **Logged in as:** `{st.session_state.user.get('username')}`")
        st.caption(f"Role: {st.session_state.user.get('role', 'player').title()}")
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()
    else:
        auth_tab_login, auth_tab_reg = st.tabs(["🔑 Login", "📝 Sign Up"])

        with auth_tab_login:
            login_user = st.text_input("Username", key="login_u")
            login_pass = st.text_input("Password", type="password", key="login_p")
            if st.button("Log In", key="btn_login", use_container_width=True):
                if login_user and login_pass:
                    ok, res = api_client.login(login_user, login_pass)
                    if ok:
                        st.session_state.token = res.get("access_token")
                        u_ok, u_res = api_client.get_current_user(st.session_state.token)
                        if u_ok:
                            st.session_state.user = u_res
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error(f"Login failed: {res}")
                else:
                    st.warning("Please enter username and password.")

        with auth_tab_reg:
            reg_user = st.text_input("Choose Username", key="reg_u")
            reg_pass = st.text_input("Choose Password", type="password", key="reg_p")
            if st.button("Create Account", key="btn_reg", use_container_width=True):
                if reg_user and reg_pass:
                    ok, res = api_client.register(reg_user, reg_pass)
                    if ok:
                        st.success("Account created! Logging you in...")
                        tok_ok, tok_res = api_client.login(reg_user, reg_pass)
                        if tok_ok:
                            st.session_state.token = tok_res.get("access_token")
                            u_ok, u_res = api_client.get_current_user(st.session_state.token)
                            if u_ok:
                                st.session_state.user = u_res
                        st.rerun()
                    else:
                        st.error(f"Registration failed: {res}")
                else:
                    st.warning("Please fill in both fields.")

    st.markdown("---")

    # Main Navigation
    nav_options = [
        "🔍 Game Bank",
        "📚 My Library",
        "⚔️ Game Workspace",
        "📤 Upload Game",
    ]
    st.session_state.nav_page = st.radio(
        "Navigation",
        options=nav_options,
        index=nav_options.index(st.session_state.nav_page) if st.session_state.nav_page in nav_options else 0,
    )


# ─── Helper: Navigate to Workspace ────────────────────────────────────────────

def open_game_workspace(game_id: int, game_name: str):
    st.session_state.selected_game_id = game_id
    st.session_state.selected_game_name = game_name
    st.session_state.nav_page = "⚔️ Game Workspace"
    st.rerun()


# ─── VIEW 1: 🔍 Game Bank (Discovery) ────────────────────────────────────────

if st.session_state.nav_page == "🔍 Game Bank":
    st.markdown('<div class="main-header">Board Game Bank</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Search available board games, filter by specifics, browse rulebooks, and curate your personal library.</div>',
        unsafe_allow_html=True,
    )

    search_query = st.text_input(
        "Search game bank by title, category, publisher, or keyword...",
        placeholder="e.g. Catan, Monopoly, Strategy, KOSMOS, trading, dice...",
        key="bank_search_input",
    )

    # Advanced Filter Bar
    with st.expander("🎯 Filter by Player Count, Category, Playtime & Complexity", expanded=False):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            selected_players = st.selectbox(
                "👥 Player Count",
                options=["Any Players", "1 Player (Solo)", "2 Players", "3 Players", "4 Players", "5 Players", "6+ Players"],
                index=0,
            )
        with col_f2:
            selected_category = st.selectbox(
                "🧩 Category / Genre",
                options=[
                    "All Categories",
                    "Strategy",
                    "Family",
                    "Party",
                    "Cooperative",
                    "Abstract Strategy",
                    "Economic",
                    "Deck-Building",
                    "Dice",
                    "Trivia",
                ],
                index=0,
            )
        with col_f3:
            selected_complexity = st.selectbox(
                "⚖️ Complexity",
                options=["All Complexities", "Light / Casual", "Medium", "Heavy / Expert"],
                index=0,
            )
        with col_f4:
            selected_playtime = st.selectbox(
                "⏱️ Max Playtime",
                options=["Any Playtime", "Under 30 min", "Under 45 min", "Under 60 min", "Under 90 min", "Under 120 min"],
                index=0,
            )

    # Map filter selections to API params
    player_param = None
    if selected_players == "1 Player (Solo)":
        player_param = 1
    elif selected_players == "2 Players":
        player_param = 2
    elif selected_players == "3 Players":
        player_param = 3
    elif selected_players == "4 Players":
        player_param = 4
    elif selected_players == "5 Players":
        player_param = 5
    elif selected_players == "6+ Players":
        player_param = 6

    playtime_param = None
    if selected_playtime == "Under 30 min":
        playtime_param = 30
    elif selected_playtime == "Under 45 min":
        playtime_param = 45
    elif selected_playtime == "Under 60 min":
        playtime_param = 60
    elif selected_playtime == "Under 90 min":
        playtime_param = 90
    elif selected_playtime == "Under 120 min":
        playtime_param = 120

    ok, games = api_client.get_games(
        q=search_query,
        players=player_param,
        category=selected_category,
        complexity=selected_complexity,
        max_playtime=playtime_param,
        token=st.session_state.token,
    )

    if not ok:
        st.error(f"Could not load game bank: {games}")
    elif not games:
        st.info("No board games found matching your search or filter criteria. Try broadening your filters or uploading a new game!")
    else:
        st.caption(f"Showing **{len(games)}** board games matching your criteria:")

        for game in games:
            with st.container():
                col_info, col_actions = st.columns([3, 1.2])

                with col_info:
                    st.markdown(f"### 🎲 **{game['name']}**")
                    render_game_metadata_badges(game)
                    if game.get("description"):
                        st.markdown(f"*{game['description']}*")
                    st.caption(f"📄 Rulebook: `{game['filename']}` | Ingested: {game['uploaded_at'][:10]}")

                with col_actions:
                    st.write("")
                    # Action 1: Open Game Workspace (Rulebook & Assistant)
                    if st.button("⚔️ Open Workspace", key=f"open_bank_{game['id']}", use_container_width=True):
                        open_game_workspace(game["id"], game["name"])

                    # Action 2: Add/Remove from Library
                    if st.session_state.token:
                        if game.get("is_in_library"):
                            if st.button("✓ In Library (Remove)", key=f"lib_rm_{game['id']}", use_container_width=True):
                                rm_ok, rm_res = api_client.remove_from_library(game["id"], st.session_state.token)
                                if rm_ok:
                                    st.success(f"Removed '{game['name']}' from library.")
                                    st.rerun()
                                else:
                                    st.error(rm_res)
                        else:
                            if st.button("★ Add to Library", key=f"lib_add_{game['id']}", use_container_width=True, type="primary"):
                                add_ok, add_res = api_client.add_to_library(game["id"], st.session_state.token)
                                if add_ok:
                                    st.success(f"Added '{game['name']}' to your library!")
                                    st.rerun()
                                else:
                                    st.error(add_res)
                    else:
                        st.caption("🔒 *Log in to save to library*")

                st.divider()


# ─── VIEW 2: 📚 My Library ────────────────────────────────────────────────────

elif st.session_state.nav_page == "📚 My Library":
    st.markdown('<div class="main-header">My Personal Library</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Your saved games for quick rulebook lookups and rules dispute assistance during game night.</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.token:
        st.warning("Please log in or create an account in the sidebar to view and manage your library.")
    else:
        ok, my_games = api_client.get_library(st.session_state.token)

        if not ok:
            st.error(f"Failed to fetch your library: {my_games}")
        elif not my_games:
            st.info("Your library is currently empty. Explore the **Game Bank** to add your favorite board games!")
            if st.button("🔍 Explore Game Bank", type="primary"):
                st.session_state.nav_page = "🔍 Game Bank"
                st.rerun()
        else:
            st.success(f"You have **{len(my_games)}** board games in your library.")

            for game in my_games:
                with st.container():
                    col_info, col_btn1, col_btn2 = st.columns([3, 1.2, 1.2])

                    with col_info:
                        st.markdown(f"### 🎲 **{game['name']}**")
                        render_game_metadata_badges(game)
                        if game.get("description"):
                            st.write(game["description"])
                        st.caption(f"File: `{game['filename']}`")

                    with col_btn1:
                        st.write("")
                        if st.button("⚔️ Launch Assistant", key=f"my_lib_open_{game['id']}", type="primary", use_container_width=True):
                            open_game_workspace(game["id"], game["name"])

                    with col_btn2:
                        st.write("")
                        if st.button("🗑️ Remove", key=f"my_lib_del_{game['id']}", use_container_width=True):
                            rm_ok, rm_res = api_client.remove_from_library(game["id"], st.session_state.token)
                            if rm_ok:
                                st.success("Removed from library.")
                                st.rerun()
                            else:
                                st.error(rm_res)

                    st.divider()


# ─── VIEW 3: ⚔️ Game Workspace (Rulebook & RAG Assistant) ─────────────────────

elif st.session_state.nav_page == "⚔️ Game Workspace":
    # Ensure available games are loaded to populate selector
    ok, all_games = api_client.get_games()
    if not ok or not all_games:
        st.warning("No board games available in the bank. Please upload a game first!")
        if st.button("Upload a Game"):
            st.session_state.nav_page = "📤 Upload Game"
            st.rerun()
    else:
        # Game Selector Header
        game_names = [g["name"] for g in all_games]
        game_map = {g["name"]: g["id"] for g in all_games}
        game_by_name = {g["name"]: g for g in all_games}

        # Determine current selection index
        current_idx = 0
        if st.session_state.selected_game_name in game_names:
            current_idx = game_names.index(st.session_state.selected_game_name)

        col_title, col_picker = st.columns([2, 1.5])
        with col_title:
            st.markdown(f'<div class="main-header">Workspace: {game_names[current_idx]}</div>', unsafe_allow_html=True)
            st.markdown('<div class="sub-header">Grounded RAG rules assistant & official rulebook viewer</div>', unsafe_allow_html=True)

        with col_picker:
            selected_name = st.selectbox(
                "Switch active game:",
                options=game_names,
                index=current_idx,
                key="workspace_game_selector",
            )
            st.session_state.selected_game_name = selected_name
            st.session_state.selected_game_id = game_map[selected_name]

        current_game_id = st.session_state.selected_game_id
        selected_game_data = game_by_name.get(selected_name, {})
        render_game_metadata_badges(selected_game_data)

        # Workspace Tabs
        tab_assistant, tab_rulebook = st.tabs(["🤖 Rules Referee (RAG Chat)", "📖 Official Rulebook"])

        # ─── Tab 1: RAG Rules Assistant ───────────────────────────────────────
        with tab_assistant:
            # Initialize chat history for this game
            if current_game_id not in st.session_state.chat_history:
                st.session_state.chat_history[current_game_id] = [
                    {
                        "role": "assistant",
                        "content": f"Hello! I am your Tabletop Sage for **{selected_name}**. Ask me any rules questions, turn sequence inquiries, or dispute clarifications!",
                        "citations": [],
                        "confidence": 1.0,
                    }
                ]

            # Render message thread
            for msg in st.session_state.chat_history[current_game_id]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

                    # Render confidence badge & citations if assistant response
                    if msg["role"] == "assistant" and msg.get("citations"):
                        conf = msg.get("confidence", 0.0)
                        if conf >= 0.65:
                            conf_badge = f'<span class="badge-confidence-high">Confidence: {int(conf * 100)}% (High)</span>'
                        elif conf >= 0.40:
                            conf_badge = f'<span class="badge-confidence-med">Confidence: {int(conf * 100)}% (Moderate)</span>'
                        else:
                            conf_badge = f'<span class="badge-confidence-low">Confidence: {int(conf * 100)}% (Low)</span>'

                        st.markdown(conf_badge, unsafe_allow_html=True)

                        with st.expander(f"📚 View {len(msg['citations'])} Rulebook Citations"):
                            for i, cit in enumerate(msg["citations"], 1):
                                st.markdown(
                                    f"**Excerpt {i} — Section: `{cit.get('section', 'Rules')}`** *(Similarity: {cit.get('score', 'N/A')})*"
                                )
                                st.markdown(f'<div class="citation-box">{cit.get("text")}</div>', unsafe_allow_html=True)

            # Chat Input for Rules Question
            if user_question := st.chat_input(f"Ask a rules question about {selected_name}..."):
                # Append and render user message
                st.session_state.chat_history[current_game_id].append({
                    "role": "user",
                    "content": user_question,
                })
                with st.chat_message("user"):
                    st.markdown(user_question)

                # Query RAG backend
                with st.chat_message("assistant"):
                    with st.spinner(f"Consulting {selected_name} rulebook and checking citations..."):
                        ask_ok, ask_res = api_client.ask_rules_question(
                            game_id=current_game_id,
                            question=user_question,
                            session_id=st.session_state.session_id,
                            token=st.session_state.token,
                        )

                        if ask_ok:
                            answer_text = ask_res.get("answer", "")
                            citations = ask_res.get("citations", [])
                            confidence = ask_res.get("confidence", 0.0)

                            st.markdown(answer_text)

                            if citations:
                                if confidence >= 0.65:
                                    conf_badge = f'<span class="badge-confidence-high">Confidence: {int(confidence * 100)}% (High)</span>'
                                elif confidence >= 0.40:
                                    conf_badge = f'<span class="badge-confidence-med">Confidence: {int(confidence * 100)}% (Moderate)</span>'
                                else:
                                    conf_badge = f'<span class="badge-confidence-low">Confidence: {int(confidence * 100)}% (Low)</span>'
                                st.markdown(conf_badge, unsafe_allow_html=True)

                                with st.expander(f"📚 View {len(citations)} Rulebook Citations"):
                                    for i, cit in enumerate(citations, 1):
                                        st.markdown(
                                            f"**Excerpt {i} — Section: `{cit.get('section', 'Rules')}`** *(Similarity: {cit.get('score', 'N/A')})*"
                                        )
                                        st.markdown(f'<div class="citation-box">{cit.get("text")}</div>', unsafe_allow_html=True)

                            # Save to session chat history
                            st.session_state.chat_history[current_game_id].append({
                                "role": "assistant",
                                "content": answer_text,
                                "citations": citations,
                                "confidence": confidence,
                            })
                        else:
                            error_text = f"⚠️ Could not retrieve answer: {ask_res}"
                            st.error(error_text)
                            st.session_state.chat_history[current_game_id].append({
                                "role": "assistant",
                                "content": error_text,
                                "citations": [],
                                "confidence": 0.0,
                            })

        # ─── Tab 2: Official Rulebook Viewer ──────────────────────────────────
        with tab_rulebook:
            rb_ok, rb_res = api_client.get_rulebook(current_game_id)
            if rb_ok:
                st.caption(f"Document source: `{rb_res.get('filename')}`")
                content = rb_res.get("content", "")
                st.text_area(
                    "Rulebook Text",
                    value=content,
                    height=550,
                    disabled=True,
                    label_visibility="collapsed",
                )
            else:
                st.error(f"Failed to load rulebook document: {rb_res}")


# ─── VIEW 4: 📤 Upload Game & Rulebook ───────────────────────────────────────

elif st.session_state.nav_page == "📤 Upload Game":
    st.markdown('<div class="main-header">Upload a Board Game</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Add a new board game and its official rulebook to the community bank. It will be automatically chunked and indexed into the ChromaDB vector store.</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.token:
        st.warning("🔒 You must be logged in to upload and index new games. Please log in using the sidebar.")
    else:
        # Show prompt to open workspace if a game was just uploaded
        if "last_uploaded_game" in st.session_state and st.session_state.last_uploaded_game:
            last_g = st.session_state.last_uploaded_game
            st.success(f"🎉 '{last_g['name']}' was successfully uploaded, chunked, and indexed into ChromaDB!")
            col_launch, col_dismiss = st.columns([2, 1])
            with col_launch:
                if st.button(f"⚔️ Launch Workspace for '{last_g['name']}'", type="primary", use_container_width=True):
                    g_id, g_name = last_g["id"], last_g["name"]
                    st.session_state.last_uploaded_game = None
                    open_game_workspace(g_id, g_name)
            with col_dismiss:
                if st.button("➕ Upload Another Game", use_container_width=True):
                    st.session_state.last_uploaded_game = None
                    st.rerun()
            st.markdown("---")

        with st.form("upload_game_form", clear_on_submit=True):
            game_title = st.text_input(
                "Board Game Title *",
                placeholder="e.g., Wingspan, Ticket to Ride, Catan, Scythe",
            )
            game_desc = st.text_area(
                "Game Description / Summary (Optional)",
                placeholder="e.g., A competitive, medium-weight, card-driven, engine-building board game.",
            )

            st.markdown("#### 🎯 Game Specifics & Details (Optional)")
            col_u1, col_u2, col_u3 = st.columns(3)
            with col_u1:
                u_min_p = st.number_input("Min Players", min_value=1, max_value=100, value=2, step=1)
                u_max_p = st.number_input("Max Players", min_value=1, max_value=100, value=4, step=1)
            with col_u2:
                u_min_age = st.number_input("Recommended Min Age (e.g. 10 for 10+)", min_value=0, max_value=120, value=10, step=1)
                u_playtime = st.number_input("Estimated Playtime (Minutes)", min_value=1, max_value=1440, value=60, step=5)
            with col_u3:
                u_category = st.selectbox(
                    "Category / Genre",
                    options=[
                        "Strategy",
                        "Family",
                        "Party",
                        "Cooperative",
                        "Abstract Strategy",
                        "Economic",
                        "Deck-Building",
                        "Dice",
                        "Trivia",
                        "Thematic",
                    ],
                    index=0,
                )
                u_complexity = st.selectbox(
                    "Complexity Level",
                    options=["Light / Casual", "Medium", "Heavy / Expert"],
                    index=1,
                )

            col_pub1, col_pub2 = st.columns(2)
            with col_pub1:
                u_publisher = st.text_input("Publisher / Game Studio (Optional)", placeholder="e.g. Stonemaier Games, Days of Wonder")
            with col_pub2:
                u_year = st.number_input("Year Published (Optional)", min_value=0, max_value=2099, value=2024, step=1)

            rulebook_file = st.file_uploader(
                "Upload Official Rulebook Document *",
                type=["txt", "md"],
                help="Upload plain text (.txt) or Markdown (.md) containing the official rules.",
            )

            submitted = st.form_submit_button("🚀 Upload & Vector Index Game", type="primary", use_container_width=True)

            if submitted:
                if not game_title or not game_title.strip():
                    st.error("Please provide a game title.")
                elif not rulebook_file:
                    st.error("Please attach a rulebook file (.txt or .md).")
                else:
                    with st.spinner("Uploading rulebook, generating embeddings, and storing in ChromaDB..."):
                        file_bytes = rulebook_file.read()
                        up_ok, up_res = api_client.upload_game(
                            name=game_title.strip(),
                            description=game_desc.strip() if game_desc else None,
                            file_bytes=file_bytes,
                            filename=rulebook_file.name,
                            token=st.session_state.token,
                            min_players=int(u_min_p) if u_min_p else None,
                            max_players=int(u_max_p) if u_max_p else None,
                            min_age=int(u_min_age) if u_min_age else None,
                            estimated_playtime=int(u_playtime) if u_playtime else None,
                            complexity=u_complexity,
                            category=u_category,
                            publisher=u_publisher.strip() if u_publisher else None,
                            year_published=int(u_year) if u_year > 0 else None,
                        )

                        if up_ok:
                            st.session_state.last_uploaded_game = {
                                "id": up_res.get("id"),
                                "name": up_res.get("name"),
                            }
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {up_res}")


