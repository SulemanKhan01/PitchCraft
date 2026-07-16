import { create } from 'zustand'

const useChatStore = create((set) => ({
  messages: [],
  input: '',
  isLoading: false,

  setMessages: (messages) => set({ messages }),

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  setInput: (input) => set({ input }),

  setIsLoading: (isLoading) => set({ isLoading }),

  clearChat: () => set({ messages: [], input: '' }),
}))

export default useChatStore
