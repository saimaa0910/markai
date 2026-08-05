/**
 * Social Studio Zustand Store — Sprint 7.5
 */
import { create } from 'zustand';
import type { SocialPlatform, SocialContentType, ScheduleType, SocialPostResponse } from '../types';

interface SocialStudioStore {
  // Platform + Content
  platform: SocialPlatform;
  contentType: SocialContentType;
  prompt: string;
  targetAudience: string;
  keywords: string[];
  brandVoice: string;
  generateImage: boolean;
  imageStyle: string;

  // Campaign
  campaignId: string | null;

  // Schedule
  scheduleType: ScheduleType;
  scheduledAt: string | null;
  timezone: string;

  // Provider / Model
  provider: string;
  model: string;
  temperature: number;

  // Editor state
  editorContent: string;
  activeTab: 'chat' | 'editor' | 'preview' | 'thread';

  // Generated result
  lastResult: SocialPostResponse | null;

  // Actions
  setPlatform: (p: SocialPlatform) => void;
  setContentType: (ct: SocialContentType) => void;
  setPrompt: (v: string) => void;
  setTargetAudience: (v: string) => void;
  setKeywords: (kw: string[]) => void;
  setBrandVoice: (v: string) => void;
  setGenerateImage: (v: boolean) => void;
  setImageStyle: (v: string) => void;
  setCampaignId: (id: string | null) => void;
  setScheduleType: (t: ScheduleType) => void;
  setScheduledAt: (dt: string | null) => void;
  setTimezone: (tz: string) => void;
  setProvider: (p: string) => void;
  setModel: (m: string) => void;
  setTemperature: (t: number) => void;
  setEditorContent: (c: string) => void;
  setActiveTab: (tab: 'chat' | 'editor' | 'preview' | 'thread') => void;
  setLastResult: (r: SocialPostResponse | null) => void;
  reset: () => void;
}

const DEFAULTS = {
  platform: 'LINKEDIN' as SocialPlatform,
  contentType: 'POST' as SocialContentType,
  prompt: '',
  targetAudience: '',
  keywords: [] as string[],
  brandVoice: '',
  generateImage: true,
  imageStyle: 'minimal',
  campaignId: null,
  scheduleType: 'DRAFT' as ScheduleType,
  scheduledAt: null,
  timezone: 'UTC',
  provider: 'google',
  model: 'gemini-1.5-flash',
  temperature: 0.75,
  editorContent: '',
  activeTab: 'chat' as const,
  lastResult: null,
};

export const useSocialStore = create<SocialStudioStore>((set) => ({
  ...DEFAULTS,
  setPlatform: (p) => set({ platform: p }),
  setContentType: (ct) => set({ contentType: ct }),
  setPrompt: (v) => set({ prompt: v }),
  setTargetAudience: (v) => set({ targetAudience: v }),
  setKeywords: (kw) => set({ keywords: kw }),
  setBrandVoice: (v) => set({ brandVoice: v }),
  setGenerateImage: (v) => set({ generateImage: v }),
  setImageStyle: (v) => set({ imageStyle: v }),
  setCampaignId: (id) => set({ campaignId: id }),
  setScheduleType: (t) => set({ scheduleType: t }),
  setScheduledAt: (dt) => set({ scheduledAt: dt }),
  setTimezone: (tz) => set({ timezone: tz }),
  setProvider: (p) => set({ provider: p }),
  setModel: (m) => set({ model: m }),
  setTemperature: (t) => set({ temperature: t }),
  setEditorContent: (c) => set({ editorContent: c }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setLastResult: (r) => set({ lastResult: r }),
  reset: () => set(DEFAULTS),
}));
