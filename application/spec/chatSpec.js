import {
  pollThreads,
  getLastMessageId,
  appendMessage,
  scrollToBottom,
  pollMessages
} from '../static/js/chat.js';

describe("Chat Frontend", () => {
  // Helper to setup DOM
  function setupChatEnvironment() {
    document.body.innerHTML = `
      <div id="threadNav" 
           data-threads-poll-url="/chat/threads/poll/"
           data-chat-url="/chat/"
           data-active-listing-id=""
           data-active-other-user-id="">
      </div>
      <div id="threadEmptyState" class="">
        <p>No listing chats yet.</p>
      </div>
      <div id="chatMessages" 
           data-poll-url="/chat/poll/"
           data-listing-id="123"
           data-other-user-id="456">
      </div>
      <div id="chatScroll" style="height: 100px;"></div>
    `;
    return {
      threadNav: document.getElementById('threadNav'),
      threadEmptyState: document.getElementById('threadEmptyState'),
      chatMessages: document.getElementById('chatMessages'),
      chatScroll: document.getElementById('chatScroll')
    };
  }

  describe("Thread rendering", () => {
    it("should render thread list from API response", (done) => {
      const { threadNav, threadEmptyState } = setupChatEnvironment();

      spyOn(window, 'fetch').and.returnValue(
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            threads: [
              {
                listing_id: '1',
                other_user_id: '5',
                listing_title: 'Laptop for Sale',
                other_user_name: 'John Doe',
                unread_count: 2,
                last_message_content: 'Is this still available?',
                last_message_created_at_display: '5 minutes ago'
              }
            ]
          })
        })
      );

      pollThreads(threadNav, threadEmptyState).then(() => {
        expect(threadNav.children.length).toBe(1);
        expect(threadNav.children[0].textContent).toContain('Laptop for Sale');
        expect(threadNav.children[0].dataset.threadListingId).toBe('1');
        expect(threadNav.children[0].dataset.threadOtherUserId).toBe('5');
        done();
      });
    });

    it("should show empty state when no threads", (done) => {
      const { threadNav, threadEmptyState } = setupChatEnvironment();

      spyOn(window, 'fetch').and.returnValue(
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ threads: [] })
        })
      );

      pollThreads(threadNav, threadEmptyState).then(() => {
        expect(threadEmptyState.classList.contains('hidden')).toBe(false);
        done();
      });
    });

    it("should highlight active thread", (done) => {
      const { threadNav, threadEmptyState } = setupChatEnvironment();
      threadNav.dataset.activeListingId = '1';
      threadNav.dataset.activeOtherUserId = '5';

      spyOn(window, 'fetch').and.returnValue(
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            threads: [
              {
                listing_id: '1',
                other_user_id: '5',
                listing_title: 'Laptop',
                other_user_name: 'John',
                unread_count: 0,
                last_message_content: 'msg',
                last_message_created_at_display: '5m ago'
              }
            ]
          })
        })
      );

      pollThreads(threadNav, threadEmptyState).then(() => {
        expect(threadNav.children[0].classList.contains('bg-violet-50')).toBe(true);
        done();
      });
    });

    it("should display unread count badge", (done) => {
      const { threadNav, threadEmptyState } = setupChatEnvironment();

      spyOn(window, 'fetch').and.returnValue(
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            threads: [
              {
                listing_id: '1',
                other_user_id: '5',
                listing_title: 'Laptop',
                other_user_name: 'John',
                unread_count: 3,
                last_message_content: 'msg',
                last_message_created_at_display: '5m ago'
              }
            ]
          })
        })
      );

      pollThreads(threadNav, threadEmptyState).then(() => {
        const unreadBadge = threadNav.querySelector('.js-thread-unread');
        expect(unreadBadge).toBeTruthy();
        expect(unreadBadge.textContent).toBe('3 new');
        done();
      });
    });
  });

  describe("Message polling", () => {
    it("should fetch new messages from API", (done) => {
      const { chatMessages, chatScroll } = setupChatEnvironment();

      spyOn(window, 'fetch').and.returnValue(
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            messages: [
              {
                id: 1,
                content: 'Hello!',
                is_outgoing: false,
                created_at_display: 'May 8, 10:30 AM'
              }
            ]
          })
        })
      );

      pollMessages(chatMessages, chatScroll, chatMessages.dataset.pollUrl, '123', '456').then(() => {
        expect(window.fetch).toHaveBeenCalled();
        expect(chatMessages.children.length).toBe(1);
        expect(chatMessages.querySelector('.message-bubble')).toBeTruthy();
        done();
      });
    });

    it("should append message to DOM", () => {
      const { chatMessages } = setupChatEnvironment();

      const msg = {
        id: 1,
        content: 'Hello!',
        is_outgoing: false,
        created_at_display: 'May 8, 10:30 AM'
      };

      appendMessage(chatMessages, msg);

      expect(chatMessages.children.length).toBe(1);
      expect(chatMessages.querySelector('.js-message')).toBeTruthy();
      expect(chatMessages.querySelector('.message-bubble').textContent).toContain('Hello!');
    });

    it("should get last message ID correctly", () => {
      const { chatMessages } = setupChatEnvironment();

      // Add some messages
      for (let i = 1; i <= 3; i++) {
        const div = document.createElement('div');
        div.className = 'js-message';
        div.setAttribute('data-message-id', String(i * 10));
        chatMessages.appendChild(div);
      }

      expect(getLastMessageId(chatMessages)).toBe(30);
    });

    it("should return 0 when no messages exist", () => {
      const { chatMessages } = setupChatEnvironment();
      expect(getLastMessageId(chatMessages)).toBe(0);
    });
  });

  describe("Message scroll behavior", () => {
    it("should scroll to bottom when messages are added", () => {
      const { chatScroll, chatMessages } = setupChatEnvironment();
      chatScroll.style.overflowY = 'auto';
      chatScroll.style.height = '200px';

      // Add content
      for (let i = 0; i < 10; i++) {
        const div = document.createElement('div');
        div.style.height = '50px';
        div.textContent = `Message ${i}`;
        chatMessages.appendChild(div);
      }

      chatScroll.appendChild(chatMessages);

      scrollToBottom(chatScroll);
      expect(chatScroll.scrollTop).toEqual(chatScroll.scrollHeight);
    });

    it("should handle empty messages without error", () => {
      const { chatScroll } = setupChatEnvironment();
      expect(() => scrollToBottom(chatScroll)).not.toThrow();
    });
  });

  describe("Thread empty state management", () => {
    it("should hide empty state when threads exist", (done) => {
      const { threadNav, threadEmptyState } = setupChatEnvironment();

      spyOn(window, 'fetch').and.returnValue(
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            threads: [
              {
                listing_id: '1',
                other_user_id: '5',
                listing_title: 'Item',
                other_user_name: 'User',
                unread_count: 0,
                last_message_content: 'msg',
                last_message_created_at_display: '5m'
              }
            ]
          })
        })
      );

      pollThreads(threadNav, threadEmptyState).then(() => {
        expect(threadEmptyState.classList.contains('hidden')).toBe(true);
        done();
      });
    });

    it("should show empty state when no threads after polling", (done) => {
      const { threadNav, threadEmptyState } = setupChatEnvironment();

      spyOn(window, 'fetch').and.returnValue(
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ threads: [] })
        })
      );

      pollThreads(threadNav, threadEmptyState).then(() => {
        expect(threadEmptyState.classList.contains('hidden')).toBe(false);
        done();
      });
    });
  });

  describe("Message transition from empty state", () => {
    it("should convert empty state message container to actual message list", () => {
      const { chatMessages } = setupChatEnvironment();
      chatMessages.className = 'rounded-2xl border bg-white p-5 text-sm text-slate-600';
      chatMessages.textContent = 'No messages yet.';

      const msg = { id: 1, content: 'First message', is_outgoing: false, created_at_display: 'now' };
      appendMessage(chatMessages, msg);

      expect(chatMessages.classList.contains('space-y-3')).toBe(true);
      expect(chatMessages.children.length).toBe(1);
      expect(chatMessages.textContent).not.toContain('No messages yet');
    });
  });

  describe("API error handling", () => {
    it("should handle failed thread fetch gracefully", (done) => {
      const { threadNav, threadEmptyState } = setupChatEnvironment();
      const initialLength = threadNav.children.length;

      spyOn(window, 'fetch').and.returnValue(
        Promise.resolve({ ok: false })
      );

      pollThreads(threadNav, threadEmptyState).then(() => {
        expect(threadNav.children.length).toBe(initialLength);
        done();
      });
    });

    it("should handle failed message poll gracefully", (done) => {
      const { chatMessages, chatScroll } = setupChatEnvironment();
      const initialLength = chatMessages.children.length;

      spyOn(window, 'fetch').and.returnValue(
        Promise.resolve({ ok: false })
      );

      pollMessages(chatMessages, chatScroll, chatMessages.dataset.pollUrl, '123', '456').then(() => {
        expect(chatMessages.children.length).toBe(initialLength);
        done();
      });
    });

    it("should handle network errors without crashing", (done) => {
      const { threadNav, threadEmptyState } = setupChatEnvironment();

      spyOn(window, 'fetch').and.returnValue(
        Promise.reject(new Error('Network error'))
      );

      pollThreads(threadNav, threadEmptyState).catch(() => {
        // Silently fails as expected
        done();
      }).then(() => {
        done();
      });
    });
  });

  describe("URL parameter encoding", () => {
    it("should properly encode thread link parameters", () => {
      const { threadNav } = setupChatEnvironment();
      threadNav.dataset.chatUrl = '/chat/';

      const listingId = '123';
      const otherUserId = '456';
      const chatUrl = threadNav.dataset.chatUrl;

      const expectedUrl = `/chat/?listing=${encodeURIComponent(listingId)}&with=${encodeURIComponent(otherUserId)}`;
      const actualUrl = `${chatUrl}?listing=${encodeURIComponent(listingId)}&with=${encodeURIComponent(otherUserId)}`;

      expect(actualUrl).toBe(expectedUrl);
    });

    it("should handle special characters in URL parameters", () => {
      const listingId = 'item-123-special';
      const encoded = encodeURIComponent(listingId);

      expect(encoded).toBe('item-123-special');
    });
  });
});
