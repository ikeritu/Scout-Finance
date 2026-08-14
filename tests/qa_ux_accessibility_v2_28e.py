#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.ui_v2_28.ui import TOKENS,contrast_ratio,css
def main():
 sheet=css();app=(Path(__file__).resolve().parents[1]/"app_v2_28.py").read_text(encoding="utf-8")
 assert contrast_ratio(TOKENS["text"],TOKENS["surface"])>=7
 assert contrast_ratio(TOKENS["primary_dark"],TOKENS["surface"])>=4.5
 assert contrast_ratio(TOKENS["warning"],TOKENS["surface"])>=4.5
 assert contrast_ratio(TOKENS["danger"],TOKENS["surface"])>=4.5
 required=("focus-visible","prefers-reduced-motion","prefers-contrast","@media(max-width:640px)","min-height:44px","Saltar al contenido principal")
 assert all(item in sheet for item in required)
 assert 'label_visibility="collapsed"' in app and '"Navegación"' in app
 assert "help=" in app and "screen_context" in app and "v2.28E" in app
 assert "unsafe_allow_html=True" in app and "apply_ui(st)" in app
 print("PASS: WCAG-contrast/focus/keyboard/labels/touch/reduced-motion/responsive/help/context");return 0
if __name__=="__main__":raise SystemExit(main())
