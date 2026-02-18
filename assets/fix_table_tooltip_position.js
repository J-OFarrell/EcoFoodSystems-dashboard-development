(function(){
  // Move Dash DataTable tooltip near the cursor and avoid viewport overflow.
  // Runs in the browser from assets/ and works for the class `.dash-table-tooltip` created by Dash.

  // Small delay to allow tooltip element to be created by Dash
  let lastVisible = null;

  document.addEventListener('mousemove', function(e){
    const tooltip = document.querySelector('.dash-table-tooltip');
    if(!tooltip) return;
    const style = window.getComputedStyle(tooltip);
    // Tooltip may exist but be hidden; only reposition when visible
    if(style.visibility === 'hidden' || style.display === 'none' || parseFloat(style.opacity) === 0) return;

    // Make sure tooltip uses fixed positioning
    tooltip.style.position = 'fixed';
    tooltip.style.pointerEvents = 'none';

    // Measure its size
    const rect = tooltip.getBoundingClientRect();
    const padding = 8;

    // Preferred position: slightly below and to the right of cursor
    let x = e.clientX + 12;
    let y = e.clientY + 18;

    // If it would overflow right edge, place to the left of cursor
    if(x + rect.width + padding > window.innerWidth) {
      x = e.clientX - rect.width - 12;
    }
    // If it would overflow bottom edge, place above cursor
    if(y + rect.height + padding > window.innerHeight) {
      y = e.clientY - rect.height - 12;
    }

    // Apply
    tooltip.style.left = Math.max(padding, x) + 'px';
    tooltip.style.top = Math.max(padding, y) + 'px';
  }, {passive: true});

  // Also reposition on scroll to keep tooltip within viewport
  window.addEventListener('scroll', function(){
    const tooltip = document.querySelector('.dash-table-tooltip');
    if(!tooltip) return;
    tooltip.style.position = 'fixed';
  }, {passive: true});

})();
