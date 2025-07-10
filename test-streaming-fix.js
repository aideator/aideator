// Simple test to verify streaming behavior
// Run this in the browser console on the streaming page

function testStreamingAnimation() {
  console.log('🎯 Testing streaming animation...');
  
  // Find the streaming container
  const streamContainer = document.querySelector('.markdown-content.streaming');
  
  if (!streamContainer) {
    console.log('❌ No streaming container found');
    return;
  }
  
  console.log('✅ Found streaming container');
  
  // Check for fade-in animation
  const computedStyle = window.getComputedStyle(streamContainer);
  console.log('📊 Container animation:', computedStyle.animation);
  
  // Check for cursor
  const cursor = document.querySelector('.streaming-cursor');
  if (cursor) {
    console.log('✅ Found streaming cursor');
    console.log('📊 Cursor animation:', window.getComputedStyle(cursor).animation);
  } else {
    console.log('❌ No streaming cursor found');
  }
  
  // Check scroll behavior
  const scrollContainer = document.querySelector('.smooth-scroll');
  if (scrollContainer) {
    console.log('✅ Found scroll container');
    console.log('📊 Scroll height:', scrollContainer.scrollHeight);
    console.log('📊 Scroll top:', scrollContainer.scrollTop);
    console.log('📊 Client height:', scrollContainer.clientHeight);
    
    // Check if auto-scroll is working
    const isAtBottom = Math.abs(scrollContainer.scrollHeight - scrollContainer.scrollTop - scrollContainer.clientHeight) < 50;
    console.log('📊 Is at bottom:', isAtBottom);
  } else {
    console.log('❌ No scroll container found');
  }
  
  // Monitor for streaming updates
  let updateCount = 0;
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'childList' || mutation.type === 'characterData') {
        updateCount++;
        console.log(`📈 Content update #${updateCount}`);
        
        // Check if container is animating
        const container = document.querySelector('.markdown-content.streaming');
        if (container) {
          const style = window.getComputedStyle(container);
          console.log('📊 Animation state:', style.animationName);
        }
      }
    });
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true
  });
  
  console.log('👀 Monitoring streaming updates...');
  
  // Stop monitoring after 30 seconds
  setTimeout(() => {
    observer.disconnect();
    console.log(`✅ Streaming test complete. Total updates: ${updateCount}`);
  }, 30000);
}

// Auto-run the test
testStreamingAnimation();