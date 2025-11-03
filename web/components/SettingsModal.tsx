"use client";
import { useCallback, useEffect, useState } from 'react';

export type Settings = {
  timezone: string;
};

export function useSettings() {
  const [settings, setSettings] = useState<Settings>({ timezone: '' });

  useEffect(() => {
    try {
      const timezone = localStorage.getItem('user_timezone') || '';
      setSettings({ timezone });
    } catch {}
  }, []);

  const persist = useCallback((s: Settings) => {
    setSettings(s);
    try {
      localStorage.setItem('user_timezone', s.timezone);
    } catch {}
  }, []);

  return { settings, setSettings: persist } as const;
}

export default function SettingsModal({
  open,
  onClose,
  settings,
  onSave,
}: {
  open: boolean;
  onClose: () => void;
  settings: Settings;
  onSave: (s: Settings) => void;
}) {
  const [timezone, setTimezone] = useState(settings.timezone);

  useEffect(() => {
    setTimezone(settings.timezone);
  }, [settings]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div className="card w-full max-w-lg p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Settings</h2>
          <button onClick={onClose} className="rounded-md p-2 hover:bg-gray-100" aria-label="Close settings">
            ✕
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Timezone</label>
            <input
              className="input"
              type="text"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              placeholder="e.g. America/New_York, Europe/London"
              readOnly={!timezone}
            />
            <p className="mt-1 text-xs text-gray-500">
              {timezone ? 'Auto-detected from browser. Edit to override.' : 'Will be auto-detected on next page load.'}
            </p>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-md px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Cancel</button>
          <button
            className="btn"
            onClick={() => {
              onSave({ timezone });
              onClose();
            }}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
