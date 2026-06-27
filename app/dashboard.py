"""Operator dashboard — Streamlit.  [PERSON C owns this file]

Landing page → "Register Missing" → File tab (operator intake).
Run:  streamlit run app/dashboard.py
"""
from __future__ import annotations
import sys
import os

# Ensure project root is on sys.path so `drishti` is importable regardless
# of how streamlit is launched (it adds app/ by default, not the root).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(page_title="Drishti", page_icon="🪔", layout="wide")

# ── query-param router: HTML links use ?navigate=app / ?navigate=landing ──────
_nav = st.query_params.get("navigate", "")
if _nav in ("app", "landing"):
    st.session_state.page = _nav
    st.query_params.clear()
    st.rerun()

if "page" not in st.session_state:
    st.session_state.page = "landing"

# ── global theme CSS (landing + app share the same palette) ───────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif; }

  .cta-btn {
    display: inline-flex; align-items: center; gap: .6rem;
    padding: .9rem 2.2rem; border-radius: 50px; text-decoration: none;
    font-size: 1.05rem; font-weight: 700;
    background: linear-gradient(135deg,#FF6B35,#FFA500); color: #fff !important;
    box-shadow: 0 8px 32px rgba(255,107,53,.38);
    transition: transform .2s, box-shadow .2s;
  }
  .cta-btn:hover { transform: translateY(-3px) scale(1.03); color:#fff !important; }
  .cta-btn-white { background: #fff !important; color: #FF6B35 !important; }
  .cta-btn-white:hover { color: #FF6B35 !important; }

  /* app: primary buttons */
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#FF6B35,#FFA500) !important;
    border: none !important; border-radius: 50px !important;
    font-weight: 700 !important; color: #fff !important;
    box-shadow: 0 4px 16px rgba(255,107,53,.35) !important;
  }
  /* app: active tab */
  [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #FF6B35 !important; border-bottom-color: #FF6B35 !important; font-weight:700 !important;
  }
  [data-testid="stMetricValue"] { color: #FF6B35 !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  LANDING PAGE
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "landing":

    st.markdown("""
    <style>
      header[data-testid="stHeader"],
      [data-testid="stSidebar"],
      [data-testid="stToolbar"],
      footer { display: none !important; }
      .main .block-container { padding: 0 !important; max-width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

    # NAV
    st.markdown("""
    <nav style="position:fixed;top:0;left:0;right:0;z-index:1000;display:flex;align-items:center;
      justify-content:space-between;padding:0 clamp(1.5rem,5vw,4rem);height:68px;
      background:rgba(255,255,255,.94);backdrop-filter:blur(14px);box-shadow:0 1px 6px rgba(0,0,0,.08);">
      <a href="#" style="display:flex;align-items:center;gap:10px;text-decoration:none;">
        <div style="width:36px;height:36px;border-radius:10px;
          background:linear-gradient(135deg,#FF6B35,#FFA500);
          display:flex;align-items:center;justify-content:center;font-size:20px;">&#x1FA94;</div>
        <span style="font-size:1.2rem;font-weight:800;letter-spacing:-.5px;
          background:linear-gradient(135deg,#FF6B35,#FFA500);
          -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">
          Drishti</span>
      </a>
      <div style="display:flex;align-items:center;gap:2rem;">
        <a href="#problem" style="font-size:.9rem;font-weight:500;color:#18181b;text-decoration:none;">The Problem</a>
        <a href="#features" style="font-size:.9rem;font-weight:500;color:#18181b;text-decoration:none;">How It Works</a>
        <a href="#proof" style="font-size:.9rem;font-weight:500;color:#18181b;text-decoration:none;">The Proof</a>
        <a href="?navigate=app" class="cta-btn" style="padding:.45rem 1.2rem;font-size:.875rem;">+ Report</a>
      </div>
    </nav>
    """, unsafe_allow_html=True)

    # HERO
    st.markdown("""
    <section id="hero" style="min-height:100vh;
      background:linear-gradient(160deg,#fff8f5 0%,#fff2e6 45%,#fffaf2 100%);
      display:flex;flex-direction:column;align-items:center;justify-content:center;
      text-align:center;padding:8rem 1.5rem 5rem;overflow:hidden;position:relative;">

      <div style="display:inline-flex;align-items:center;gap:8px;padding:6px 16px;
        border-radius:50px;background:rgba(255,107,53,.10);border:1px solid rgba(255,107,53,.22);
        font-size:.78rem;font-weight:700;color:#FF6B35;text-transform:uppercase;
        letter-spacing:.06em;margin-bottom:1.5rem;">
        <span style="width:7px;height:7px;border-radius:50%;background:#FF6B35;display:inline-block;"></span>
        Nashik Kumbh Mela 2027 &middot; Claude Impact Lab
      </div>

      <h1 style="font-size:clamp(2.6rem,8vw,5.2rem);font-weight:900;line-height:1.06;
        letter-spacing:-2.5px;max-width:880px;margin:0 0 1.5rem;color:#18181b;">
        Reunite the
        <span style="background:linear-gradient(135deg,#FF6B35,#FFA500);
          -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">
          missing</span><br>without surveilling anyone
      </h1>

      <p style="font-size:clamp(1rem,2.5vw,1.2rem);color:#52525b;max-width:600px;
        margin:0 auto 2.5rem;line-height:1.78;">
        One shared, live, de-identified registry that connects the two halves of every
        search &mdash; the family looking and the person found &mdash; across centers that
        today can&apos;t see each other, in any language, on weak data.
        <strong>No face scans. No GPS tracking.</strong>
      </p>

      <div style="margin-bottom:3.5rem;">
        <a href="?navigate=app" class="cta-btn">
          <span style="font-size:1.25em;font-weight:800;">+</span>
          Report the Missing Person
          <span style="font-size:1.15em;">&rarr;</span>
        </a>
      </div>

      <div style="display:flex;gap:2.5rem;justify-content:center;flex-wrap:wrap;">
        <div><div style="font-size:2rem;font-weight:900;
          background:linear-gradient(135deg,#FF6B35,#FFA500);-webkit-background-clip:text;
          background-clip:text;-webkit-text-fill-color:transparent;">~10</div>
          <div style="font-size:.78rem;color:#52525b;font-weight:500;margin-top:3px;">Centers Unified</div></div>
        <div><div style="font-size:2rem;font-weight:900;
          background:linear-gradient(135deg,#FF6B35,#FFA500);-webkit-background-clip:text;
          background-clip:text;-webkit-text-fill-color:transparent;">202</div>
          <div style="font-size:.78rem;color:#52525b;font-weight:500;margin-top:3px;">Real Validation Rows</div></div>
        <div><div style="font-size:2rem;font-weight:900;
          background:linear-gradient(135deg,#FF6B35,#FFA500);-webkit-background-clip:text;
          background-clip:text;-webkit-text-fill-color:transparent;">0</div>
          <div style="font-size:.78rem;color:#52525b;font-weight:500;margin-top:3px;">Faces Scanned</div></div>
        <div><div style="font-size:2rem;font-weight:900;
          background:linear-gradient(135deg,#FF6B35,#FFA500);-webkit-background-clip:text;
          background-clip:text;-webkit-text-fill-color:transparent;">Offline</div>
          <div style="font-size:.78rem;color:#52525b;font-weight:500;margin-top:3px;">Core Matcher Runs</div></div>
      </div>

      <div style="width:100%;overflow:hidden;line-height:0;margin-top:4rem;">
        <svg viewBox="0 0 1440 80" preserveAspectRatio="none" style="display:block;width:100%;">
          <path d="M0,40 C240,80 480,0 720,40 C960,80 1200,0 1440,40 L1440,80 L0,80 Z" fill="#18181b"/>
        </svg>
      </div>
    </section>
    """, unsafe_allow_html=True)

    # PROBLEM (dark)
    st.markdown("""
    <section id="problem" style="background:#18181b;padding:clamp(4rem,8vw,7rem) 0;
      position:relative;overflow:hidden;">
      <div style="max-width:1160px;margin:0 auto;padding:0 clamp(1.5rem,5vw,3rem);">
        <p style="font-size:.78rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
          color:#FF6B35;margin-bottom:1rem;">The Challenge</p>
        <h2 style="font-size:clamp(1.8rem,4.5vw,2.8rem);font-weight:800;letter-spacing:-1px;
          line-height:1.15;margin-bottom:1rem;color:#fff;">
          Ten centers.<br><span style="color:#FFA500;">None of them can see each other.</span>
        </h2>
        <p style="font-size:1.05rem;color:rgba(255,255,255,.58);line-height:1.82;
          max-width:640px;margin-bottom:3rem;">
          A person <em>found</em> at Center B is invisible to a family <em>searching</em> at
          Center A. The lost person is often elderly or a child, non-literate, panicking,
          doesn&apos;t speak the local language &mdash; and usually cannot identify themselves.
          Names and phone numbers are missing or useless.
        </p>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1.25rem;">
          <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);
            border-radius:16px;padding:1.75rem;">
            <div style="font-size:2rem;font-weight:900;background:linear-gradient(135deg,#FF6B35,#FFA500);
              -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
              margin-bottom:.5rem;">Silos</div>
            <div style="font-size:1rem;font-weight:700;color:#fff;margin-bottom:.4rem;">Disconnected Centers</div>
            <p style="font-size:.875rem;color:rgba(255,255,255,.5);line-height:1.65;margin:0;">
              Each camp keeps its own paper list. A match across the grounds stays unseen for hours.
            </p>
          </div>
          <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);
            border-radius:16px;padding:1.75rem;">
            <div style="font-size:2rem;font-weight:900;background:linear-gradient(135deg,#FF6B35,#FFA500);
              -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
              margin-bottom:.5rem;">No ID</div>
            <div style="font-size:1rem;font-weight:700;color:#fff;margin-bottom:.4rem;">Weak Signals Only</div>
            <p style="font-size:.875rem;color:rgba(255,255,255,.5);line-height:1.65;margin:0;">
              All you have is age, gender, language, location, and a physical description.
            </p>
          </div>
          <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);
            border-radius:16px;padding:1.75rem;">
            <div style="font-size:2rem;font-weight:900;background:linear-gradient(135deg,#FF6B35,#FFA500);
              -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
              margin-bottom:.5rem;">Many langs</div>
            <div style="font-size:1rem;font-weight:700;color:#fff;margin-bottom:.4rem;">Across Languages</div>
            <p style="font-size:.875rem;color:rgba(255,255,255,.5);line-height:1.65;margin:0;">
              &ldquo;Saffron saree, rudraksha&rdquo; and &ldquo;orange clothes, prayer beads&rdquo;
              describe the same person &mdash; no rule-based system connects them.
            </p>
          </div>
        </div>
      </div>
      <div style="width:100%;overflow:hidden;line-height:0;">
        <svg viewBox="0 0 1440 80" preserveAspectRatio="none" style="display:block;width:100%;">
          <path d="M0,40 C240,0 480,80 720,40 C960,0 1200,80 1440,40 L1440,80 L0,80 Z" fill="#ffffff"/>
        </svg>
      </div>
    </section>
    """, unsafe_allow_html=True)

    # FEATURES
    st.markdown("""
    <section id="features" style="background:#fff;padding:clamp(4rem,8vw,7rem) 0;">
      <div style="max-width:1160px;margin:0 auto;padding:0 clamp(1.5rem,5vw,3rem);">
        <p style="font-size:.78rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
          color:#FF6B35;margin-bottom:1rem;">Our Solution</p>
        <h2 style="font-size:clamp(1.8rem,4.5vw,2.8rem);font-weight:800;letter-spacing:-1px;
          line-height:1.15;margin-bottom:1rem;color:#18181b;">Match the reports,<br>not the people</h2>
        <p style="font-size:1.05rem;color:#52525b;max-width:580px;line-height:1.75;margin-bottom:3.5rem;">
          Claude is the brain. Privacy is structural. The whole thing runs offline.
        </p>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.5rem;">
          <div style="background:#fafafa;border:1.5px solid rgba(0,0,0,.06);border-radius:16px;padding:2rem;">
            <div style="font-size:2rem;margin-bottom:1rem;">&#x2699;&#xFE0F;</div>
            <div style="font-size:1.1rem;font-weight:700;margin-bottom:.5rem;color:#18181b;">Claude Cross-Lingual Matching</div>
            <p style="font-size:.9rem;color:#52525b;line-height:1.72;margin:0 0 1rem;">
              Structures voice intake and matches descriptions across languages &mdash;
              and explains every match so an operator can trust it.
            </p>
            <span style="padding:4px 12px;border-radius:50px;font-size:.72rem;font-weight:700;
              background:rgba(255,107,53,.10);color:#FF6B35;text-transform:uppercase;">The Brain</span>
          </div>
          <div style="background:#fafafa;border:1.5px solid rgba(0,0,0,.06);border-radius:16px;padding:2rem;">
            <div style="font-size:2rem;margin-bottom:1rem;">&#x1F512;</div>
            <div style="font-size:1.1rem;font-weight:700;margin-bottom:.5rem;color:#18181b;">Privacy That&apos;s Structural</div>
            <p style="font-size:.9rem;color:#52525b;line-height:1.72;margin:0 0 1rem;">
              Name and mobile are hashed at ingest. Identity is revealed only at a
              human-confirmed reunion and raw PII is purged afterward.
            </p>
            <span style="padding:4px 12px;border-radius:50px;font-size:.72rem;font-weight:700;
              background:rgba(255,107,53,.10);color:#FF6B35;text-transform:uppercase;">Reveal on Confirm</span>
          </div>
          <div style="background:#fafafa;border:1.5px solid rgba(0,0,0,.06);border-radius:16px;padding:2rem;">
            <div style="font-size:2rem;margin-bottom:1rem;">&#x1F4E1;</div>
            <div style="font-size:1.1rem;font-weight:700;margin-bottom:.5rem;color:#18181b;">Offline-First, No GPU</div>
            <p style="font-size:.9rem;color:#52525b;line-height:1.72;margin:0 0 1rem;">
              The core matcher runs with pandas + stdlib only &mdash; no network, no API key, no GPU.
              Capture never blocks.
            </p>
            <span style="padding:4px 12px;border-radius:50px;font-size:.72rem;font-weight:700;
              background:rgba(255,107,53,.10);color:#FF6B35;text-transform:uppercase;">Runs Anywhere</span>
          </div>
        </div>
      </div>
    </section>
    """, unsafe_allow_html=True)

    # WHAT WE DON'T DO
    st.markdown("""
    <section id="boundary" style="background:#fff7f3;padding:clamp(4rem,8vw,7rem) 0;">
      <div style="max-width:1160px;margin:0 auto;padding:0 clamp(1.5rem,5vw,3rem);">
        <p style="font-size:.78rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
          color:#FF6B35;margin-bottom:1rem;">The Honest Boundary</p>
        <h2 style="font-size:clamp(1.8rem,4.5vw,2.8rem);font-weight:800;letter-spacing:-1px;
          line-height:1.15;margin-bottom:1rem;color:#18181b;">
          What we deliberately<br>do <span style="color:#FF6B35;">not</span> do
        </h2>
        <p style="font-size:1.05rem;color:#52525b;max-width:600px;line-height:1.75;margin-bottom:3rem;">
          We don&apos;t track the person and we don&apos;t scan faces. A human always
          brings them to a help point &mdash; we just make that fast.
        </p>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.5rem;">
          <div style="background:#fff;border-radius:20px;padding:2rem;
            box-shadow:0 4px 24px rgba(0,0,0,.10);border:1px solid rgba(255,107,53,.07);">
            <div style="font-size:1.5rem;margin-bottom:.75rem;">&#x1F6AB;</div>
            <div style="font-size:1.05rem;font-weight:700;margin-bottom:.5rem;color:#18181b;">No facial recognition</div>
            <p style="font-size:.93rem;color:#52525b;line-height:1.78;margin:0;">
              CCTV input is coordinates only &mdash; no footage, no faces.
              We predict <em>where to look</em>, never who is who.
            </p>
          </div>
          <div style="background:#fff;border-radius:20px;padding:2rem;
            box-shadow:0 4px 24px rgba(0,0,0,.10);border:1px solid rgba(255,107,53,.07);">
            <div style="font-size:1.5rem;margin-bottom:.75rem;">&#x1F4CD;</div>
            <div style="font-size:1.05rem;font-weight:700;margin-bottom:.5rem;color:#18181b;">No GPS tracking</div>
            <p style="font-size:.93rem;color:#52525b;line-height:1.78;margin:0;">
              The lost person carries no device. We match <em>reports</em> about them,
              not a live location feed.
            </p>
          </div>
          <div style="background:#fff;border-radius:20px;padding:2rem;
            box-shadow:0 4px 24px rgba(0,0,0,.10);border:1px solid rgba(255,107,53,.07);">
            <div style="font-size:1.5rem;margin-bottom:.75rem;">&#x1F91D;</div>
            <div style="font-size:1.05rem;font-weight:700;margin-bottom:.5rem;color:#18181b;">A human always confirms</div>
            <p style="font-size:.93rem;color:#52525b;line-height:1.78;margin:0;">
              Identity is revealed only at a confirmed reunion. A blind-spot map
              places help where separations cluster.
            </p>
          </div>
        </div>
      </div>
    </section>
    """, unsafe_allow_html=True)

    # THE PROOF
    st.markdown("""
    <section id="proof" style="background:#fff;padding:clamp(4rem,8vw,7rem) 0;">
      <div style="max-width:1160px;margin:0 auto;padding:0 clamp(1.5rem,5vw,3rem);">
        <p style="font-size:.78rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
          color:#FF6B35;margin-bottom:1rem;">The Number That Proves It</p>
        <h2 style="font-size:clamp(1.8rem,4.5vw,2.8rem);font-weight:800;letter-spacing:-1px;
          line-height:1.15;margin-bottom:1rem;color:#18181b;">A real metric,<br>not a demo</h2>
        <p style="font-size:1.05rem;color:#52525b;max-width:600px;line-height:1.75;margin-bottom:2.5rem;">
          Almost no team brings a real number.
          <code style="background:#fff2e6;padding:1px 6px;border-radius:5px;">validate.py</code>
          runs offline in seconds against 202 real duplicate-report rows.
        </p>
        <div style="background:#18181b;border-radius:16px;padding:1.75rem 2rem;
          font-family:monospace;color:#fafafa;overflow-x:auto;
          box-shadow:0 16px 52px rgba(0,0,0,.18);margin-bottom:2rem;">
          <div style="color:rgba(255,255,255,.4);font-size:.8rem;margin-bottom:.75rem;"># run THE NUMBER, offline, in seconds</div>
          <div style="font-size:.95rem;line-height:2;">
            <span style="color:#FFA500;">$</span> python -m drishti.ingest
            <span style="color:rgba(255,255,255,.4);">&nbsp;&nbsp;# seeded 2500 records</span>
          </div>
          <div style="font-size:.95rem;line-height:2;">
            <span style="color:#FFA500;">$</span> python -m drishti.validate
            <span style="color:rgba(255,255,255,.4);">&nbsp;# THE NUMBER</span>
          </div>
          <div style="font-size:.95rem;line-height:2;">
            <span style="color:#FFA500;">$</span> streamlit run app/dashboard.py
            <span style="color:rgba(255,255,255,.4);">&nbsp;# operator UI</span>
          </div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:1.25rem;">
          <div style="background:#fafafa;border:1.5px solid rgba(0,0,0,.06);border-radius:16px;padding:1.5rem;">
            <div style="font-size:1.8rem;font-weight:900;background:linear-gradient(135deg,#FF6B35,#FFA500);
              -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">Method A</div>
            <p style="font-size:.875rem;color:#52525b;line-height:1.65;margin:.4rem 0 0;">
              Recall against 202 real <code>is_duplicate_report</code> rows.
            </p>
          </div>
          <div style="background:#fafafa;border:1.5px solid rgba(0,0,0,.06);border-radius:16px;padding:1.5rem;">
            <div style="font-size:1.8rem;font-weight:900;background:linear-gradient(135deg,#FF6B35,#FFA500);
              -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">Method B</div>
            <p style="font-size:.875rem;color:#52525b;line-height:1.65;margin:.4rem 0 0;">
              Discrimination gap on synthetic recovered pairs.
            </p>
          </div>
          <div style="background:#fafafa;border:1.5px solid rgba(0,0,0,.06);border-radius:16px;padding:1.5rem;">
            <div style="font-size:1.8rem;font-weight:900;background:linear-gradient(135deg,#FF6B35,#FFA500);
              -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">Seconds</div>
            <p style="font-size:.875rem;color:#52525b;line-height:1.65;margin:.4rem 0 0;">
              No network, no API key, no GPU. The differentiator.
            </p>
          </div>
        </div>
      </div>
    </section>
    """, unsafe_allow_html=True)

    # HOW IT WORKS
    st.markdown("""
    <section id="how" style="background:#fff7f3;padding:clamp(4rem,8vw,7rem) 0;">
      <div style="max-width:1160px;margin:0 auto;padding:0 clamp(1.5rem,5vw,3rem);">
        <p style="font-size:.78rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
          color:#FF6B35;margin-bottom:1rem;">Architecture &middot; One Screen</p>
        <h2 style="font-size:clamp(1.8rem,4.5vw,2.8rem);font-weight:800;letter-spacing:-1px;
          line-height:1.15;margin-bottom:1rem;color:#18181b;">
          From a lost report<br>to a confirmed reunion
        </h2>
        <p style="font-size:1.05rem;color:#52525b;max-width:600px;line-height:1.75;margin-bottom:3.5rem;">
          Voice-first intake feeds one shared registry. Intelligence runs on top.
          A human always closes the loop.
        </p>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
          gap:2rem;text-align:center;">
          <div>
            <div style="width:56px;height:56px;border-radius:50%;
              background:linear-gradient(135deg,#FF6B35,#FFA500);color:#fff;font-size:1.3rem;
              font-weight:900;display:flex;align-items:center;justify-content:center;
              margin:0 auto 1.25rem;box-shadow:0 8px 32px rgba(255,107,53,.38);">1</div>
            <div style="font-size:1rem;font-weight:700;margin-bottom:.5rem;color:#18181b;">Intake</div>
            <p style="font-size:.875rem;color:#52525b;line-height:1.65;margin:0;">
              Operator asks &ldquo;Lost?&rdquo; or &ldquo;Found?&rdquo; Voice-first.
              Name and mobile are hashed immediately.
            </p>
          </div>
          <div>
            <div style="width:56px;height:56px;border-radius:50%;
              background:linear-gradient(135deg,#FF6B35,#FFA500);color:#fff;font-size:1.3rem;
              font-weight:900;display:flex;align-items:center;justify-content:center;
              margin:0 auto 1.25rem;box-shadow:0 8px 32px rgba(255,107,53,.38);">2</div>
            <div style="font-size:1rem;font-weight:700;margin-bottom:.5rem;color:#18181b;">The Registry</div>
            <p style="font-size:.875rem;color:#52525b;line-height:1.65;margin:0;">
              One shared, live, de-identified pool. Every report from any center lands
              here and breaks the silos.
            </p>
          </div>
          <div>
            <div style="width:56px;height:56px;border-radius:50%;
              background:linear-gradient(135deg,#FF6B35,#FFA500);color:#fff;font-size:1.3rem;
              font-weight:900;display:flex;align-items:center;justify-content:center;
              margin:0 auto 1.25rem;box-shadow:0 8px 32px rgba(255,107,53,.38);">3</div>
            <div style="font-size:1rem;font-weight:700;margin-bottom:.5rem;color:#18181b;">Intelligence</div>
            <p style="font-size:.875rem;color:#52525b;line-height:1.65;margin:0;">
              Tier-1 offline rules + Tier-2 Claude cross-lingual matching + drift
              predictor + blind-spot map.
            </p>
          </div>
          <div>
            <div style="width:56px;height:56px;border-radius:50%;
              background:linear-gradient(135deg,#FF6B35,#FFA500);color:#fff;font-size:1.3rem;
              font-weight:900;display:flex;align-items:center;justify-content:center;
              margin:0 auto 1.25rem;box-shadow:0 8px 32px rgba(255,107,53,.38);">4</div>
            <div style="font-size:1rem;font-weight:700;margin-bottom:.5rem;color:#18181b;">Reunite</div>
            <p style="font-size:.875rem;color:#52525b;line-height:1.65;margin:0;">
              A human confirms the match &mdash; only then is identity revealed,
              and raw PII is purged.
            </p>
          </div>
        </div>
      </div>
    </section>
    """, unsafe_allow_html=True)

    # FINAL CTA
    st.markdown("""
    <section id="cta" style="padding:clamp(5rem,10vw,9rem) 1.5rem;text-align:center;
      background:linear-gradient(135deg,#FF6B35 0%,#FFA500 100%);
      position:relative;overflow:hidden;">
      <div style="position:absolute;top:-50%;left:-10%;width:600px;height:600px;
        border-radius:50%;background:rgba(255,255,255,.07);pointer-events:none;"></div>
      <h2 style="font-size:clamp(2rem,5vw,3.5rem);font-weight:900;color:#fff;
        letter-spacing:-1.5px;line-height:1.1;margin-bottom:1rem;position:relative;z-index:1;">
        Connect the two halves<br>of every search
      </h2>
      <p style="font-size:1.1rem;color:rgba(255,255,255,.85);max-width:560px;
        margin:0 auto 2.5rem;line-height:1.72;position:relative;z-index:1;">
        Built for the Claude Impact Lab, Mumbai 2026. Open source, offline-first,
        designed so no one is ever surveilled.
      </p>
      <div style="position:relative;z-index:1;margin-bottom:1.5rem;">
        <a href="?navigate=app" class="cta-btn cta-btn-white">Register Missing Person</a>
      </div>
      <p style="font-size:.8rem;color:rgba(255,255,255,.65);position:relative;z-index:1;">
        No face scans &middot; No GPS tracking &middot; Runs offline
      </p>
    </section>

    <footer style="background:#18181b;padding:3rem clamp(1.5rem,5vw,4rem);">
      <div style="max-width:1160px;margin:0 auto;display:flex;align-items:center;
        justify-content:space-between;flex-wrap:wrap;gap:1.5rem;">
        <div style="display:flex;align-items:center;gap:10px;">
          <div style="width:32px;height:32px;border-radius:9px;
            background:linear-gradient(135deg,#FF6B35,#FFA500);
            display:flex;align-items:center;justify-content:center;font-size:17px;">&#x1FA94;</div>
          <span style="font-size:1rem;font-weight:800;background:linear-gradient(135deg,#FF6B35,#FFA500);
            -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">Drishti</span>
        </div>
        <span style="font-size:.825rem;color:rgba(255,255,255,.4);">
          The Problem &nbsp;&middot;&nbsp; How It Works &nbsp;&middot;&nbsp; The Proof
        </span>
      </div>
      <div style="max-width:1160px;margin:2rem auto 0;border-top:1px solid rgba(255,255,255,.08);
        padding-top:1.5rem;display:flex;justify-content:space-between;flex-wrap:wrap;gap:1rem;">
        <p style="font-size:.8rem;color:rgba(255,255,255,.35);margin:0;">
          &copy; 2026 Drishti &middot; Claude Impact Lab, Mumbai 2026
        </p>
        <p style="font-size:.8rem;color:rgba(255,255,255,.28);margin:0;">
          Made with <span style="color:#FF6B35;">&#9829;</span> for Nashik Kumbh Mela 2027
        </p>
      </div>
    </footer>
    """, unsafe_allow_html=True)

    st.stop()  # nothing below runs on the landing page


# ═══════════════════════════════════════════════════════════════════════════════
#  OPERATOR APP
# ═══════════════════════════════════════════════════════════════════════════════
from drishti import config as C
from drishti import i18n


def _api():
    from drishti import api
    return api


def _ensure():
    try:
        api = _api()
        msg = api.ensure_seeded()
        return api, msg, None
    except Exception as e:
        return None, None, str(e)


api, seed_msg, init_err = _ensure()

with st.sidebar:
    st.markdown("""
    <a href="?navigate=landing" style="display:flex;align-items:center;gap:8px;
      text-decoration:none;margin-bottom:1rem;">
      <div style="width:30px;height:30px;border-radius:8px;
        background:linear-gradient(135deg,#FF6B35,#FFA500);
        display:flex;align-items:center;justify-content:center;font-size:16px;">&#x1FA94;</div>
      <span style="font-weight:800;background:linear-gradient(135deg,#FF6B35,#FFA500);
        -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">
        Drishti</span>
    </a>
    """, unsafe_allow_html=True)

    ui_lang = st.selectbox("🌐 " + i18n.EN["ui_lang"], list(i18n.UI_LANGS),
                           help="Translates the whole interface.")
    T = i18n.translator(ui_lang)
    st.divider()
    st.subheader("🗄️ " + T("registry_live"))
    if init_err:
        st.error(f"DB not connected: {init_err}")
    else:
        s = api.stats()
        st.metric(T("records"), s["total"])
        st.caption(f"open {s['open']} · reunited {s['reunited']} · "
                   f"{s['centers']} centers · {s['languages']} languages")
        st.caption(f"vault: {s['vault_live']} live / {s['vault_purged']} purged (raw PII, 0600)")
        if "demo" in (seed_msg or ""):
            st.info("Demo data (data/ is empty). Drop the real CSV to replace.")
        if st.button("🔁 Reset demo data", use_container_width=True):
            api.reset()
            st.rerun()

st.title("🪔 Drishti — Nashik Kumbh 2027")
st.caption(T("tagline"))

tab_file, tab_registry, tab_matches, tab_maps, tab_validation, tab_mesh = st.tabs(
    [T("tab_file"), T("tab_registry"), T("tab_matches"),
     T("tab_maps"), T("tab_validation"), T("tab_mesh")]
)

# ── File (intake) ─────────────────────────────────────────────────────────────
with tab_file:
    st.header(T("file_header"))
    st.caption(T("nothing_mandatory"))
    if init_err:
        st.error(f"DB not connected: {init_err}")
    else:
        import base64
        import datetime
        import uuid
        from drishti import geo, llm, privacy, voice
        from drishti.ingest import Record

        def _idx(options, value, default=0):
            try:
                return options.index(value)
            except (ValueError, AttributeError):
                return default

        def _clean(x):
            return "" if not x or x in ("Unknown", "—") else x

        def _say(text_en, lang_name):
            spoken = voice.translate(text_en, target_code=voice.lang_code(lang_name))
            return spoken, voice.speak(spoken, voice.lang_code(lang_name))

        fork = st.radio(T("what_happened"), [T("lost"), T("found")], horizontal=True)
        langs = list(C.SARVAM_LANG_CODES.keys())
        lang = st.selectbox(T("reporter_lang"), langs,
                            index=_idx(langs, (st.session_state.get("voice") or {})
                                       .get("fields", {}).get("language")))
        asr = ("Sarvam" if voice.have_sarvam() else
               "local Whisper (free)" if voice.have_asr() else "unavailable")
        brain = "Claude" if llm.have_claude() else "built-in heuristics"

        st.markdown("##### " + T("voice_assistant") + f"  ·  _ASR: {asr} · {brain}_")
        vmode = st.radio("vmode", [T("live_convo"), "⚡ One-shot"],
                         horizontal=True, label_visibility="collapsed")

        if vmode == "⚡ One-shot":
            if st.button(f"{T('ask_in')} {lang}"):
                st.session_state["ask"] = _say(voice.assistant_prompt(), lang)
            ask = st.session_state.get("ask")
            if ask:
                st.info(f"🗣️ {ask[0]}")
                if ask[1]:
                    st.audio(base64.b64decode(ask[1]), format="audio/mp3", autoplay=True)
            clip = st.audio_input(T("record_answer"))
            if clip is not None:
                st.session_state["clip_bytes"] = clip.getvalue()
                if st.button(T("understand_fill")):
                    with st.spinner(f"{asr} + {brain}…"):
                        st.session_state["voice"] = voice.voice_to_fields(clip)
        else:
            qs = voice.CONVO_QUESTIONS
            convo = st.session_state.setdefault("convo", {"turn": -1, "collected": {},
                                                           "history": [], "q_text": "", "q_audio": None})

            def _ask_turn(i):
                convo["q_text"], convo["q_audio"] = _say(qs[i], lang)

            if convo["turn"] < 0:
                if st.button("▶ " + T("live_convo"), type="primary"):
                    convo["turn"] = 0
                    _ask_turn(0)
                    st.rerun()
            elif convo["turn"] < len(qs):
                turn = convo["turn"]
                st.info(f"🗣️ ({turn + 1}/{len(qs)}) {convo['q_text']}")
                if convo["q_audio"]:
                    st.audio(base64.b64decode(convo["q_audio"]), format="audio/mp3", autoplay=True)
                ans = st.audio_input(T("record_answer"), key=f"ans{turn}")
                b1, b2 = st.columns(2)
                if ans is not None and b1.button("✅ Answer → next question"):
                    st.session_state["clip_bytes"] = ans.getvalue()
                    with st.spinner(f"{asr} + {brain}…"):
                        txt = voice.transcribe_to_english(ans)
                        ext = (voice.structure_report(txt) or voice._heuristic_fields(txt)) if txt else {}
                        convo["collected"] = voice.merge_fields(convo["collected"], ext)
                        convo["history"].append(txt or "")
                    convo["turn"] += 1
                    if convo["turn"] < len(qs):
                        _ask_turn(convo["turn"])
                    st.rerun()
                if b2.button("⏭ Skip / finish"):
                    convo["turn"] = len(qs)
                    st.rerun()
            else:
                st.success("✅ Conversation complete — review the fields below and file.")
                if st.button("🔄 Restart conversation"):
                    st.session_state.pop("convo", None)
                    st.rerun()
            st.session_state["voice"] = {
                "transcript": " · ".join(t for t in convo.get("history", []) if t),
                "fields": convo.get("collected", {}), "asr": True,
                "structured": llm.have_claude()}
            if convo.get("collected"):
                st.caption("📋 " + " · ".join(f"**{k}**: {vv}" for k, vv in convo["collected"].items()))

        v = st.session_state.get("voice") or {}
        vf = v.get("fields", {}) if v else {}
        if v.get("transcript") and vmode == "⚡ One-shot":
            st.success('🗣️ Heard (→ English): "' + v["transcript"] + '"')

        st.markdown("##### " + T("details_optional"))
        r1, r2, r3 = st.columns(3)
        reporter_name = r1.text_input(T("your_name"), value=vf.get("reporter_name", ""))
        relation = r2.text_input(T("relation"), value=vf.get("relation", ""),
                                 placeholder="son, wife, friend…")
        person_name = r3.text_input(T("their_name"), value=vf.get("missing_person_name", ""))

        g1, g2, g3 = st.columns(3)
        gender = g1.selectbox(T("gender"), ["Unknown", "Male", "Female"],
                              index=_idx(["Unknown", "Male", "Female"], vf.get("gender")))
        age_opts = ["—"] + C.AGE_ORDER
        age = g2.selectbox(T("age"), age_opts, index=_idx(age_opts, vf.get("age_band")))
        try:
            booth_names = [p.name for p in geo.load_points()]
            seen_near = g3.selectbox(T("last_seen"), booth_names,
                                     index=_idx(booth_names, vf.get("last_seen_location")))
        except Exception:
            seen_near = g3.text_input(T("last_seen"), vf.get("last_seen_location", ""))

        h1, h2, h3 = st.columns(3)
        height = h1.selectbox(T("height"), ["Unknown", "Tall", "Average", "Short"],
                              index=_idx(["Unknown", "Tall", "Average", "Short"], vf.get("height")))
        build = h2.selectbox(T("build"), ["Unknown", "Thin", "Average", "Heavy"],
                             index=_idx(["Unknown", "Thin", "Average", "Heavy"], vf.get("build")))
        complexion = h3.selectbox(T("complexion"), ["Unknown", "Fair", "Medium", "Dark"],
                                  index=_idx(["Unknown", "Fair", "Medium", "Dark"], vf.get("complexion")))
        hr1, hr2 = st.columns(2)
        hair_len = hr1.selectbox(T("hair_length"), ["Unknown", "Long", "Short", "Bald"],
                                 index=_idx(["Unknown", "Long", "Short", "Bald"], vf.get("hair_length")))
        hair_color = hr2.text_input(T("hair_color"), value=vf.get("hair_color", ""),
                                    placeholder="black, grey, white…")
        clothing = st.text_input(T("wearing"), value=vf.get("clothing", ""),
                                 placeholder="saffron kurta, blue saree…")
        marks = st.text_input(T("marks"), value=vf.get("marks", ""),
                              placeholder="mole, scar, walking stick, glasses, hard of hearing")
        notes = st.text_area(T("anything_else"), value="")
        mobile = st.text_input(T("contact"), value="")

        if st.button(T("file_report"), type="primary"):
            case_id = "KMP-2027-" + uuid.uuid4().hex[:5].upper()
            rtype = "missing" if fork.startswith("🔍") else "found"
            bits = [b for b in [
                _clean(height) and f"{height.lower()} height",
                _clean(build) and f"{build.lower()} build",
                _clean(hair_len) and f"{hair_len.lower()} hair",
                _clean(hair_color) and f"{hair_color} hair",
                _clean(complexion) and f"{complexion.lower()} complexion",
                _clean(clothing), _clean(marks), _clean(notes),
            ] if b]
            desc = ", ".join(bits) or vf.get("physical_description", "")
            rep = "; ".join(b for b in [
                reporter_name and f"reporter: {reporter_name}",
                relation and f"relation: {relation}"] if b)
            rec = Record(
                case_id=case_id,
                reported_at=datetime.datetime.now().isoformat(timespec="minutes"),
                gender=gender, age_band=_clean(age), state="", district="", language=lang,
                last_seen_location=seen_near, reporting_center="Booth Intake",
                physical_description=desc, status="Pending",
                name_hash=privacy.hash_pii(person_name), mobile_hash=privacy.hash_pii(mobile),
                remarks=rep, vault_id=case_id, report_type=rtype)
            try:
                api.file_report(rec, name=person_name or None, mobile=mobile or None)
                st.success(f"Filed **{case_id}** → registry + vault. Slip printed.")
            except Exception as e:
                st.error(f"Persist failed: {e}")
            if st.session_state.get("clip_bytes"):
                d = C.ROOT / "data" / "voice_clips"
                d.mkdir(parents=True, exist_ok=True)
                (d / f"{case_id}.wav").write_bytes(st.session_state["clip_bytes"])
                st.caption(f"🎙️ Voice recording saved with {case_id}.")
            try:
                payload = geo.broadcast_alert(seen_near, radius_m=1000)
                st.warning(f"🚨 Emergency signal → **{payload['count']} booths** within "
                           f"1 km of *{seen_near}*: "
                           + ", ".join(b["name"] for b in payload["alerted_booths"][:8]))
            except Exception:
                pass
            if rtype == "found":
                txt, audio = voice.containment_message(lang)
                st.info(f'🔊 Spoken to the found person in {lang}: "{txt}"')
                if audio:
                    st.audio(base64.b64decode(audio), format="audio/mp3")
            try:
                ms = api.find_matches(case_id, top_k=3)
                if ms:
                    st.markdown("**Instant matches in the open pool:**")
                    for m in ms:
                        st.write(f"• {m['case_id']} — score {m['score']:.0f} "
                                 f"({'🟢 strong' if m['is_strong'] else '🟡 weak'})")
            except Exception:
                pass

# ── Registry ──────────────────────────────────────────────────────────────────
with tab_registry:
    st.header(T("registry_header"))
    if init_err:
        st.error(f"DB not connected: {init_err}")
    else:
        only_open = st.toggle("Show only open (matchable) cases", value=False)
        recs = api.list_records(open_only=only_open, limit=300)
        st.caption(f"{len(recs)} records — de-identified (no name/mobile; those live "
                   "hashed in the vault and surface only at reunion).")
        st.dataframe(
            [{"case_id": r.case_id, "type": r.report_type, "gender": r.gender,
              "age": r.age_band, "language": r.language,
              "location": r.last_seen_location, "center": r.reporting_center,
              "status": r.status, "reported_at": r.reported_at}
             for r in recs],
            use_container_width=True, hide_index=True,
        )

# ── Matches ───────────────────────────────────────────────────────────────────
with tab_matches:
    st.header(T("matches_header"))
    if init_err:
        st.error(f"DB not connected: {init_err}")
    else:
        open_recs = api.list_records(open_only=True)
        if not open_recs:
            st.warning("No open cases in the registry.")
        else:
            labels = {f"{r.case_id} · {r.report_type} · {r.gender} {r.age_band} · "
                      f"{r.language} @ {r.last_seen_location} ({r.reporting_center})": r.case_id
                      for r in open_recs}
            picked = st.selectbox("Pick an open report to match", list(labels))
            case_id = labels[picked]
            target = api.get_record(case_id)
            st.caption(f'"{target.physical_description}"')

            matches = api.find_matches(case_id, top_k=3)
            if not matches:
                st.info("No candidates in the time-windowed open pool yet.")
            for m in matches:
                if m["score"] >= C.MATCH_AUTO:
                    band = "🟢 AUTO"
                elif m["score"] >= C.MATCH_REVIEW:
                    band = "🟡 REVIEW"
                else:
                    band = "⚪ low"
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(
                        f"**{m['case_id']}** · {m['report_type']} · {m['gender']} "
                        f"{m['age_band']} · {m['language']} @ {m['last_seen_location']} "
                        f'· _{m["reporting_center"]}_  \n"{m["physical_description"]}"')
                    c2.metric("score", f"{m['score']:.0f}", band)
                    st.caption("why: " + " · ".join(f"{k}+{v}" for k, v in m["reasons"].items()))
                    if st.button(f"✅ Confirm reunion: {case_id} ↔ {m['case_id']}",
                                 key=f"confirm_{case_id}_{m['case_id']}"):
                        res = api.confirm(case_id, m["case_id"], actor="operator",
                                          reason="operator-confirmed at help point")
                        st.session_state["last_confirm"] = res
                        st.rerun()

            res = st.session_state.get("last_confirm")
            if res:
                st.success(f"🎉 {res['summary']} — both marked Reunited.")
                contacts = [f"{c}: {v.get('reporter_mobile') or '—'} "
                            f"({v.get('missing_person_name') or 'unnamed'})"
                            for c, v in res["revealed"].items()]
                st.markdown("**Revealed contact (call now):** " +
                            (" · ".join(contacts) if contacts else "—"))
                st.caption(f"Raw PII purged from the vault for {res['purged']} "
                           "(hash kept). Every reveal/purge is in audit.log.")
                if st.button("Dismiss"):
                    del st.session_state["last_confirm"]
                    st.rerun()

# ── Maps ──────────────────────────────────────────────────────────────────────
with tab_maps:
    st.header("🗺️ " + T("maps_header"))
    try:
        from drishti import geo, drift, blindspot
        from streamlit_folium import st_folium
        names = [p.name for p in geo.load_points()]
        d_idx = names.index("Ramkund Ghat") if "Ramkund Ghat" in names else 0
        mt1, mt2, mt3 = st.tabs(["🚨 Live broadcast", "🧭 Drift predictor", "📷 Blind-spot map"])

        with mt1:
            left, right = st.columns([1, 2])
            with left:
                origin = st.selectbox("A report comes in near…", names, index=d_idx, key="bc")
                radius = st.slider("Emergency radius (m)", 300, 2000, 1000, 100)
                payload = geo.broadcast_alert(origin, radius_m=radius)
                st.metric("🚨 Booths alerted", payload["count"])
                st.caption("Every booth in the radius gets the signal.")
                for b in payload["alerted_booths"][:12]:
                    st.write(f"• {b['name']} — {b['distance_m']} m")
            with right:
                st_folium(geo.build_map(highlight=origin, radius_m=radius),
                          height=480, use_container_width=True, returned_objects=[])

        with mt2:
            st.caption("Bounded by walking speed (~1–2 km/h) + behavioural priors.")
            d1, d2, d3 = st.columns(3)
            ls = d1.selectbox("Last seen near", names, index=d_idx, key="dr")
            prof = d2.selectbox("Profile", ["elderly", "child", "adult"])
            elapsed = d3.slider("Missing for (hours)", 0.5, 8.0, 2.0, 0.5)
            for z in drift.predict(ls, elapsed, prof, top_k=6):
                st.write(f"**{z['probability']*100:.0f}%** · {z['name']} "
                         f"({z['distance_m']} m, {z['type']})")
            st.caption("elderly → anchor landmarks · child → close & erratic · adult → exits")

        with mt3:
            st.caption("High crowd-separation × few cameras = where people vanish unseen.")
            l, r = st.columns([1, 2])
            with l:
                for d in blindspot.rank_blind_spots(top_k=10):
                    st.write(f"🚨 **{d['name']}** — pressure {d['pressure']}, {d['cameras']} cams")
            with r:
                st_folium(blindspot.build_map(top_k=12), height=480,
                          use_container_width=True, returned_objects=[])
    except Exception as e:
        st.warning("Maps need folium + streamlit-folium in the venv.\n\n" + str(e))

# ── Validation ────────────────────────────────────────────────────────────────
with tab_validation:
    st.header(T("validation_header"))
    if st.button(T("run_validation")):
        try:
            from drishti.validate import run
            with st.spinner("scoring…"):
                res = run()
            st.json(res)
        except Exception as e:
            st.error(f"Need data/ populated to run validation on real data: {e}")

# ── Mesh ──────────────────────────────────────────────────────────────────────
with tab_mesh:
    st.header("📡 " + T("mesh_header"))
    st.caption("Capture NEVER blocks. LAN down: booths sync peer-to-peer. "
               "Worst case: one SMS carries the report.")
    from drishti import mesh, sms
    if st.button("▶ Run booth↔booth P2P sim (LAN-loss fallback)"):
        res = mesh.run_demo()
        for e in res["events"]:
            st.write(e)
        st.success(f"Converged (terminal-status-wins): {res['converged']} · "
                   f"central state: {res['final']}")
    st.divider()
    st.markdown("##### 📨 SMS bridge (no-signal fallback)")
    st.caption("A low-end phone / field radio sends: TYPE|GENDER|AGE|STATE|LOCATION")
    line = st.text_input("Inbound SMS", "MISSING|F|65|Bihar|SectorB")
    parsed = sms.parse_inbound(line)
    st.write("parsed →", parsed or "invalid format")
