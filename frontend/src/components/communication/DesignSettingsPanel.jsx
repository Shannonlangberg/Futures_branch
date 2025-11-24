import React, { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';

const DesignSettingsPanel = ({ settings, onChange }) => {
  const [expandedSections, setExpandedSections] = useState({
    emailBody: true,
    fonts: true
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const updateSetting = (key, value) => {
    onChange({
      ...settings,
      [key]: value
    });
  };

  return (
    <div className="w-80 bg-slate-800 border-l border-white/10 p-4 overflow-y-auto">
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-white/40 text-xs">Content</span>
          <span className="text-white font-semibold text-sm">Design</span>
        </div>
      </div>

      {/* EMAIL BODY & BACKGROUND */}
      <div className="mb-4">
        <button
          onClick={() => toggleSection('emailBody')}
          className="w-full flex items-center justify-between p-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
        >
          <span className="text-white font-semibold text-sm">EMAIL BODY & BACKGROUND</span>
          {expandedSections.emailBody ? (
            <ChevronUpIcon className="w-4 h-4 text-white/60" />
          ) : (
            <ChevronDownIcon className="w-4 h-4 text-white/60" />
          )}
        </button>

        {expandedSections.emailBody && (
          <div className="mt-2 space-y-3 p-2">
            {/* Email Width */}
            <div>
              <label className="block text-white/60 text-xs mb-1">Email Width</label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={settings.emailWidth}
                  onChange={(e) => updateSetting('emailWidth', parseInt(e.target.value) || 567)}
                  className="flex-1 px-2 py-1 bg-white/5 border border-white/10 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <label className="flex items-center gap-1 text-white/60 text-xs">
                  <input
                    type="checkbox"
                    checked={settings.evenColumns}
                    onChange={(e) => updateSetting('evenColumns', e.target.checked)}
                    className="w-4 h-4"
                  />
                  Even Columns
                </label>
              </div>
            </div>

            {/* Full width on mobile */}
            <div>
              <label className="flex items-center gap-2 text-white/60 text-xs">
                <input
                  type="checkbox"
                  checked={settings.fullWidthMobile}
                  onChange={(e) => updateSetting('fullWidthMobile', e.target.checked)}
                  className="w-4 h-4"
                />
                Full width on mobile
              </label>
            </div>

            {/* Grid Width */}
            <div>
              <label className="block text-white/60 text-xs mb-1">Grid Width</label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={settings.gridWidth}
                  onChange={(e) => updateSetting('gridWidth', parseInt(e.target.value) || 25)}
                  className="flex-1 px-2 py-1 bg-white/5 border border-white/10 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <label className="flex items-center gap-1 text-white/60 text-xs">
                  <input
                    type="checkbox"
                    checked={settings.useGrid}
                    onChange={(e) => updateSetting('useGrid', e.target.checked)}
                    className="w-4 h-4"
                  />
                  Use Grid
                </label>
              </div>
            </div>

            {/* Border */}
            <div>
              <label className="block text-white/60 text-xs mb-1">Border</label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={settings.borderColor}
                  onChange={(e) => updateSetting('borderColor', e.target.value)}
                  className="w-10 h-8 rounded border border-white/20 cursor-pointer"
                />
                <input
                  type="text"
                  value={settings.borderColor}
                  onChange={(e) => updateSetting('borderColor', e.target.value)}
                  className="flex-1 px-2 py-1 bg-white/5 border border-white/10 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="number"
                  value={settings.borderWidth}
                  onChange={(e) => updateSetting('borderWidth', parseInt(e.target.value) || 0)}
                  className="w-16 px-2 py-1 bg-white/5 border border-white/10 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Background Colour */}
            <div>
              <label className="block text-white/60 text-xs mb-1 flex items-center gap-1">
                Background Colour
                <span className="text-white/40">?</span>
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={settings.backgroundColor}
                  onChange={(e) => updateSetting('backgroundColor', e.target.value)}
                  className="w-10 h-8 rounded border border-white/20 cursor-pointer"
                />
                <input
                  type="text"
                  value={settings.backgroundColor}
                  onChange={(e) => updateSetting('backgroundColor', e.target.value)}
                  className="flex-1 px-2 py-1 bg-white/5 border border-white/10 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Full height background */}
            <div>
              <label className="flex items-center gap-2 text-white/60 text-xs">
                <input
                  type="checkbox"
                  checked={settings.fullHeightBackground}
                  onChange={(e) => updateSetting('fullHeightBackground', e.target.checked)}
                  className="w-4 h-4"
                />
                Full height background colour
              </label>
            </div>

            {/* Background Image */}
            <div>
              <label className="block text-white/60 text-xs mb-1 flex items-center gap-1">
                Background Image
                <span className="text-white/40">?</span>
              </label>
              <input
                type="text"
                value={settings.backgroundImage || ''}
                onChange={(e) => updateSetting('backgroundImage', e.target.value)}
                placeholder="Select Image"
                className="w-full px-2 py-1 bg-white/5 border border-white/10 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* DEFAULT FONTS */}
      <div>
        <button
          onClick={() => toggleSection('fonts')}
          className="w-full flex items-center justify-between p-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
        >
          <span className="text-white font-semibold text-sm">DEFAULT FONTS</span>
          {expandedSections.fonts ? (
            <ChevronUpIcon className="w-4 h-4 text-white/60" />
          ) : (
            <ChevronDownIcon className="w-4 h-4 text-white/60" />
          )}
        </button>

        {expandedSections.fonts && (
          <div className="mt-2 space-y-3 p-2">
            {/* Body Text */}
            <div>
              <label className="block text-white/60 text-xs mb-1">Body Text</label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={settings.bodyTextColor}
                  onChange={(e) => updateSetting('bodyTextColor', e.target.value)}
                  className="w-10 h-8 rounded border border-white/20 cursor-pointer"
                />
                <select
                  value={settings.bodyFont}
                  onChange={(e) => updateSetting('bodyFont', e.target.value)}
                  className="flex-1 px-2 py-1 bg-white/5 border border-white/10 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Arial" className="bg-slate-800">Arial</option>
                  <option value="Helvetica" className="bg-slate-800">Helvetica</option>
                  <option value="Georgia" className="bg-slate-800">Georgia</option>
                  <option value="Times New Roman" className="bg-slate-800">Times New Roman</option>
                  <option value="Verdana" className="bg-slate-800">Verdana</option>
                  <option value="Courier New" className="bg-slate-800">Courier New</option>
                </select>
                <input
                  type="number"
                  value={settings.bodyFontSize}
                  onChange={(e) => updateSetting('bodyFontSize', parseInt(e.target.value) || 12)}
                  className="w-16 px-2 py-1 bg-white/5 border border-white/10 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Line Height */}
            <div>
              <label className="block text-white/60 text-xs mb-1">Line Height</label>
              <select
                value={settings.lineHeight}
                onChange={(e) => updateSetting('lineHeight', parseFloat(e.target.value))}
                className="w-full px-2 py-1 bg-white/5 border border-white/10 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="1" className="bg-slate-800">1</option>
                <option value="1.25" className="bg-slate-800">1.25</option>
                <option value="1.5" className="bg-slate-800">1.5</option>
                <option value="1.75" className="bg-slate-800">1.75</option>
                <option value="2" className="bg-slate-800">2</option>
              </select>
            </div>

            {/* Links */}
            <div>
              <label className="block text-white/60 text-xs mb-1">Links</label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={settings.linkColor || '#000000'}
                  onChange={(e) => updateSetting('linkColor', e.target.value)}
                  className="w-10 h-8 rounded border border-white/20 cursor-pointer"
                />
                <div className="flex gap-1">
                  <button
                    onClick={() => updateSetting('linkBold', !settings.linkBold)}
                    className={`px-2 py-1 rounded text-xs ${settings.linkBold ? 'bg-blue-500 text-white' : 'bg-white/5 text-white/60'}`}
                  >
                    B
                  </button>
                  <button
                    onClick={() => updateSetting('linkItalic', !settings.linkItalic)}
                    className={`px-2 py-1 rounded text-xs ${settings.linkItalic ? 'bg-blue-500 text-white' : 'bg-white/5 text-white/60'}`}
                  >
                    I
                  </button>
                  <button
                    onClick={() => updateSetting('linkUnderline', !settings.linkUnderline)}
                    className={`px-2 py-1 rounded text-xs ${settings.linkUnderline ? 'bg-blue-500 text-white' : 'bg-white/5 text-white/60'}`}
                  >
                    U
                  </button>
                </div>
              </div>
            </div>

            {/* Heading 1 + Header component */}
            <div>
              <label className="block text-white/60 text-xs mb-1">Heading 1 + Header component</label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={settings.headingColor || settings.bodyTextColor}
                  onChange={(e) => updateSetting('headingColor', e.target.value)}
                  className="w-10 h-8 rounded border border-white/20 cursor-pointer"
                />
                <select
                  value={settings.headingFont || settings.bodyFont}
                  onChange={(e) => updateSetting('headingFont', e.target.value)}
                  className="flex-1 px-2 py-1 bg-white/5 border border-white/10 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Arial" className="bg-slate-800">Arial</option>
                  <option value="Helvetica" className="bg-slate-800">Helvetica</option>
                  <option value="Georgia" className="bg-slate-800">Georgia</option>
                  <option value="Times New Roman" className="bg-slate-800">Times New Roman</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DesignSettingsPanel;

