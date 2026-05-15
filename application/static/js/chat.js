/**
 * Chat module for handling thread and message polling
 * Manages real-time chat updates and DOM manipulation
 */

/**
 * Fetches and renders thread list from API
 * @param {HTMLElement} threadNav - The thread navigation container
 * @param {HTMLElement} emptyState - The empty state element
 * @returns {Promise<void>}
 */
export async function pollThreads(threadNav, emptyState) {
  if (!threadNav) return;

  const threadsPollUrl = threadNav.dataset.threadsPollUrl;
  const chatUrl = threadNav.dataset.chatUrl;
  const activeListingId = String(threadNav.dataset.activeListingId || '');
  const activeOtherUserId = String(threadNav.dataset.activeOtherUserId || '');
  
  if (!threadsPollUrl || !chatUrl) return;

  try {
    const res = await fetch(threadsPollUrl, { headers: { 'Accept': 'application/json' } });
    if (!res.ok) return;
    
    const data = await res.json();
    const threads = (data && Array.isArray(data.threads)) ? data.threads : [];

    threadNav.textContent = '';

    if (emptyState) {
      if (threads.length > 0) emptyState.classList.add('hidden');
      else emptyState.classList.remove('hidden');
    }

    for (const t of threads) {
      const listingId = String(t.listing_id);
      const otherUserId = String(t.other_user_id);
      const isActive = listingId === activeListingId && otherUserId === activeOtherUserId;

      const a = document.createElement('a');
      a.href = `${chatUrl}?listing=${encodeURIComponent(listingId)}&with=${encodeURIComponent(otherUserId)}`;
      a.dataset.threadListingId = listingId;
      a.dataset.threadOtherUserId = otherUserId;
      a.className = 'block rounded-2xl border px-4 py-3 mb-2 hover:bg-slate-50 ' + (isActive ? 'border-violet-200 bg-violet-50' : 'border-slate-200 bg-white');

      const topRow = document.createElement('div');
      topRow.className = 'flex items-start justify-between gap-3';

      const left = document.createElement('div');
      left.className = 'min-w-0';

      const title = document.createElement('p');
      title.className = 'truncate text-sm font-semibold text-slate-900';
      title.textContent = t.listing_title || '';

      const withLine = document.createElement('p');
      withLine.className = 'truncate text-xs text-slate-600';
      withLine.textContent = `With ${t.other_user_name || ''}`;

      left.appendChild(title);
      left.appendChild(withLine);

      const right = document.createElement('div');
      right.className = 'shrink-0 text-right';

      const time = document.createElement('p');
      time.className = 'js-thread-time text-[11px] text-slate-500';
      time.textContent = t.last_message_created_at_display || '';
      right.appendChild(time);

      const unreadCount = Number(t.unread_count || 0);
      if (unreadCount > 0) {
        const unread = document.createElement('span');
        unread.className = 'js-thread-unread mt-1 inline-flex items-center rounded-full bg-violet-600 px-2 py-0.5 text-[11px] font-semibold text-white';
        unread.textContent = `${unreadCount} new`;
        right.appendChild(unread);
      } else {
        const read = document.createElement('span');
        read.className = 'js-thread-read mt-1 inline-flex items-center gap-1 text-[11px] text-slate-400';

        const dot = document.createElement('span');
        dot.className = 'inline-block h-1.5 w-1.5 rounded-full bg-slate-300';

        const label = document.createElement('span');
        label.textContent = 'read';

        read.appendChild(dot);
        read.appendChild(label);
        right.appendChild(read);
      }

      topRow.appendChild(left);
      topRow.appendChild(right);

      const preview = document.createElement('p');
      preview.className = 'js-thread-preview mt-2 truncate text-xs text-slate-500';
      preview.textContent = t.last_message_content || '';

      a.appendChild(topRow);
      a.appendChild(preview);
      threadNav.appendChild(a);
    }
  } catch (e) {
    // fail silently
  }
}

/**
 * Gets the ID of the last message in the chat
 * @param {HTMLElement} messagesRoot - The messages container
 * @returns {number} The last message ID or 0
 */
export function getLastMessageId(messagesRoot) {
  if (!messagesRoot) return 0;
  
  const nodes = messagesRoot.querySelectorAll('.js-message[data-message-id]');
  if (!nodes.length) return 0;
  
  const last = nodes[nodes.length - 1];
  const raw = last.getAttribute('data-message-id');
  const id = parseInt(raw || '0', 10);
  
  return Number.isFinite(id) ? id : 0;
}

/**
 * Appends a message to the chat
 * @param {HTMLElement} messagesRoot - The messages container
 * @param {Object} msg - Message object with id, content, is_outgoing, created_at_display
 */
export function appendMessage(messagesRoot, msg) {
  if (!messagesRoot) return;
  
  // Ensure container exists even when there were no messages
  if (!messagesRoot.classList.contains('space-y-3')) {
    messagesRoot.className = 'space-y-3';
    messagesRoot.textContent = '';
  }

  const outer = document.createElement('div');
  outer.className = 'js-message';
  outer.dataset.messageId = String(msg.id);

  const row = document.createElement('div');
  row.className = 'flex ' + (msg.is_outgoing ? 'justify-end' : 'justify-start');

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble max-w-[85%] rounded-2xl px-4 py-2 text-sm shadow-sm ' + (msg.is_outgoing ? 'bg-violet-600 text-white' : 'bg-white text-slate-900 border');

  const p = document.createElement('p');
  p.className = 'whitespace-pre-wrap break-words';
  p.textContent = msg.content;

  const meta = document.createElement('p');
  meta.className = 'mt-1 text-[11px] ' + (msg.is_outgoing ? 'text-violet-100' : 'text-slate-400');
  meta.textContent = msg.created_at_display || '';

  bubble.appendChild(p);
  bubble.appendChild(meta);
  row.appendChild(bubble);
  outer.appendChild(row);
  messagesRoot.appendChild(outer);
}

/**
 * Scrolls chat container to bottom
 * @param {HTMLElement} scrollBox - The scrollable container
 */
export function scrollToBottom(scrollBox) {
  if (!scrollBox) return;
  scrollBox.scrollTop = scrollBox.scrollHeight;
}

/**
 * Polls for new messages from API
 * @param {HTMLElement} messagesRoot - The messages container
 * @param {HTMLElement} scrollBox - The scrollable container
 * @param {string} pollUrl - Base URL for polling
 * @param {string} listingId - Listing ID
 * @param {string} otherUserId - Other user ID
 * @returns {Promise<void>}
 */
export async function pollMessages(messagesRoot, scrollBox, pollUrl, listingId, otherUserId) {
  if (!messagesRoot || !pollUrl || !listingId || !otherUserId) return;

  const afterId = getLastMessageId(messagesRoot);
  const url = new URL(pollUrl, window.location.origin);
  url.searchParams.set('listing', listingId);
  url.searchParams.set('with', otherUserId);
  url.searchParams.set('after_id', String(afterId));

  try {
    const res = await fetch(url.toString(), { headers: { 'Accept': 'application/json' } });
    if (!res.ok) return;
    
    const data = await res.json();
    if (!data || !Array.isArray(data.messages) || data.messages.length === 0) return;

    for (const m of data.messages) {
      appendMessage(messagesRoot, m);
    }
    scrollToBottom(scrollBox);
  } catch (e) {
    // fail silently; next poll will retry
  }
}

/**
 * Initializes chat polling on page load
 * Should be called once when chat page is ready
 */
export function initChat() {
  const threadNav = document.getElementById('threadNav');
  const emptyState = document.getElementById('threadEmptyState');
  const messagesRoot = document.getElementById('chatMessages');
  const scrollBox = document.getElementById('chatScroll');

  // Initial thread poll
  if (threadNav) {
    pollThreads(threadNav, emptyState);
    window.setInterval(() => pollThreads(threadNav, emptyState), 7000);
  }

  // Initial message poll and scrolling
  if (messagesRoot && scrollBox) {
    const pollUrl = messagesRoot.dataset.pollUrl;
    const listingId = messagesRoot.dataset.listingId;
    const otherUserId = messagesRoot.dataset.otherUserId;

    if (pollUrl && listingId && otherUserId) {
      scrollToBottom(scrollBox);
      window.setInterval(() => pollMessages(messagesRoot, scrollBox, pollUrl, listingId, otherUserId), 5000);
    }
  }
}
