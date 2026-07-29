(function(){
  // Makes the floating chatbot widget (#chatbot-widget-wrapper, containing
  // both the toggle button and the panel) draggable anywhere on screen as a
  // SINGLE unit - drag from either the button or the panel header, and both
  // move together, since both are positioned relative to the same wrapper.
  // Also handles opening/closing the panel. Runs entirely client-side, not
  // via a Dash callback: mixing Dash-managed style updates with JS-driven
  // drag positioning on the same element risks Dash's virtual DOM silently
  // overwriting the dragged position on any unrelated re-render, so this
  // file owns the wrapper's `style` completely (see app.py's Chatbot
  // Assistant Callbacks comment).

  // The wrapper's own box collapses to ~0x0 (its children are all
  // position: absolute, so they don't contribute to its size) - use fixed
  // assumed dimensions for on-screen clamping instead of the wrapper's own
  // (unreliable) offsetWidth/offsetHeight. The wrapper's (left, top) is the
  // BUTTON's bottom-left corner (button has bottom:0/left:0 on the wrapper);
  // the panel sits ABOVE that point (bottom: 66px on the wrapper), so the
  // panel - not the button - is what can go off the TOP of the screen, and
  // the button - not the panel - is what can go off the BOTTOM.
  var PANEL_WIDTH = 340;
  var PANEL_HEIGHT = 470;
  var PANEL_BOTTOM_OFFSET = 66; // matches PANEL_STYLE_BASE's "bottom" in chatbot_ui.py
  var BUTTON_SIZE = 56;

  function attachDragHandle(wrapper, handle) {
    let dragging = false;
    let moved = false;
    let startX = 0, startY = 0, origLeft = 0, origTop = 0;

    handle.addEventListener('mousedown', function(e){
      dragging = true;
      moved = false;
      const rect = wrapper.getBoundingClientRect();
      startX = e.clientX;
      startY = e.clientY;
      origLeft = rect.left;
      origTop = rect.top;
      e.preventDefault();
    });

    document.addEventListener('mousemove', function(e){
      if (!dragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      if (Math.abs(dx) > 4 || Math.abs(dy) > 4) moved = true;
      if (!moved) return;

      let newLeft = origLeft + dx;
      let newTop = origTop + dy;

      // Horizontal: both button and panel extend rightward from the same
      // left edge; the wider panel is the binding constraint.
      const maxLeft = Math.max(0, window.innerWidth - PANEL_WIDTH);
      newLeft = Math.min(Math.max(0, newLeft), maxLeft);

      // Vertical: keep the panel's top on-screen (wrapper top can't go
      // above panelHeight + its offset), and keep the button's bottom
      // on-screen (wrapper top can't exceed the viewport height). If the
      // viewport is too short to satisfy both, prioritize the button - it's
      // the persistent, always-visible affordance.
      const minTop = PANEL_BOTTOM_OFFSET + PANEL_HEIGHT;
      const maxTop = window.innerHeight;
      const effectiveMinTop = Math.min(minTop, maxTop);
      newTop = Math.min(Math.max(effectiveMinTop, newTop), maxTop);

      wrapper.style.left = newLeft + 'px';
      wrapper.style.top = newTop + 'px';
      wrapper.style.right = 'auto';
      wrapper.style.bottom = 'auto';
    });

    document.addEventListener('mouseup', function(){
      if (dragging && moved) {
        // A real drag happened - the browser fires an automatic click on
        // the handle right after this mouseup (same target for both), as
        // part of the same user gesture. Flag it so the handle's own click
        // handler (see setup()) can ignore just that one click, instead of
        // toggling the panel open/closed when the user only meant to
        // reposition it. The flag is cleared on the next tick rather than
        // after a fixed delay - the automatic click always arrives
        // synchronously in the same task as this mouseup, so a delay much
        // longer than that (e.g. a flat 1s) risks swallowing a later,
        // genuinely separate click the user makes soon after releasing the
        // drag.
        handle.dataset.suppressNextClick = '1';
        setTimeout(function(){
          delete handle.dataset.suppressNextClick;
        }, 0);
      }
      dragging = false;
    });
  }

  function setup(){
    const wrapper = document.getElementById('chatbot-widget-wrapper');
    const btn = document.getElementById('chatbot-toggle-btn');
    const panel = document.getElementById('chatbot-panel');
    const header = document.getElementById('chatbot-panel-header');
    const closeBtn = document.getElementById('chatbot-close-btn');

    if (!wrapper || !btn || !panel || !header || !closeBtn) {
      // Dash renders async - keep retrying until the widget exists.
      setTimeout(setup, 300);
      return;
    }
    if (wrapper.dataset.chatbotDragInit) return;
    wrapper.dataset.chatbotDragInit = '1';

    // Both handles drag the SAME wrapper, so button + panel move as one unit.
    attachDragHandle(wrapper, btn);
    attachDragHandle(wrapper, header);

    btn.addEventListener('click', function(){
      if (btn.dataset.suppressNextClick) {
        delete btn.dataset.suppressNextClick;
        return;
      }
      const isOpen = panel.style.display === 'block';
      panel.style.display = isOpen ? 'none' : 'block';
    });

    closeBtn.addEventListener('click', function(e){
      e.stopPropagation();
      panel.style.display = 'none';
    });
  }

  document.addEventListener('DOMContentLoaded', setup);
  setup();
})();
