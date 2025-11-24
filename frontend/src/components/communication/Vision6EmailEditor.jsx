import React, { useState, useRef, useEffect } from 'react';
import {
  PhotoIcon,
  VideoCameraIcon,
  LinkIcon,
  Bars3Icon,
  TrashIcon,
  PlusIcon,
  GlobeAltIcon,
  RectangleStackIcon,
  DocumentTextIcon,
  PlayIcon,
  Squares2X2Icon,
  MinusIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const Vision6EmailEditor = ({ value, onChange, designSettings, onDesignSettingsChange }) => {
  const [blocks, setBlocks] = useState([]);
  const [draggedBlock, setDraggedBlock] = useState(null);
  const [selectedBlock, setSelectedBlock] = useState(null);
  const [showImageDialog, setShowImageDialog] = useState(false);
  const [showVideoDialog, setShowVideoDialog] = useState(false);
  const [showLinkDialog, setShowLinkDialog] = useState(false);
  const [imageType, setImageType] = useState('regular');
  const [videoUrl, setVideoUrl] = useState('');
  const [linkUrl, setLinkUrl] = useState('');
  const [linkText, setLinkText] = useState('');
  const fileInputRef = useRef(null);
  const headerImageInputRef = useRef(null);
  const textBlockRefs = useRef({});

  const defaultDesignSettings = {
    emailWidth: 567,
    evenColumns: true,
    fullWidthMobile: false,
    gridWidth: 25,
    useGrid: false,
    borderColor: '#FFFFFF',
    borderWidth: 0,
    backgroundColor: '#E8E6E6',
    fullHeightBackground: false,
    backgroundImage: null,
    bodyTextColor: '#2A2A2A',
    bodyFont: 'Arial',
    bodyFontSize: 12,
    lineHeight: 1.5,
    linkColor: null,
    linkBold: false,
    linkItalic: false,
    linkUnderline: false
  };

  const settings = { ...defaultDesignSettings, ...designSettings };

  useEffect(() => {
    try {
      if (value) {
        parseHTMLToBlocks(value);
      } else {
        setBlocks([{ id: Date.now(), type: 'text', content: '<p>Start typing your email content here...</p>' }]);
      }
    } catch (error) {
      console.error('Error initializing blocks:', error);
      // Fallback to empty block
      setBlocks([{ id: Date.now(), type: 'text', content: '<p>Start typing your email content here...</p>' }]);
    }
  }, []);

  useEffect(() => {
    try {
      const html = blocksToHTML(blocks);
      onChange(html);
    } catch (error) {
      console.error('Error converting blocks to HTML:', error);
      // Don't call onChange with invalid HTML
    }
  }, [blocks]);

  const parseHTMLToBlocks = (html) => {
    try {
      if (!html || typeof html !== 'string') {
        return [{ id: Date.now(), type: 'text', content: '<p>Start typing your email content here...</p>' }];
      }
      
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      const body = doc.body;
      
      if (!body) {
        return [{ id: Date.now(), type: 'text', content: '<p>Start typing your email content here...</p>' }];
      }
      
      const blockArray = [];
      let blockId = Date.now();

    // Check for header image first
    const headerImg = body.querySelector('img[data-type="header"]');
    if (headerImg) {
      blockArray.push({
        id: blockId++,
        type: 'header-image',
        content: headerImg.outerHTML
      });
    }

    // Parse other elements
    Array.from(body.children).forEach(child => {
      if (child.tagName === 'IMG' && !child.hasAttribute('data-type')) {
        blockArray.push({
          id: blockId++,
          type: 'image',
          content: child.outerHTML
        });
      } else if (child.tagName === 'IFRAME' || child.querySelector('iframe')) {
        blockArray.push({
          id: blockId++,
          type: 'video',
          content: child.outerHTML
        });
      } else if (child.innerHTML.trim()) {
        blockArray.push({
          id: blockId++,
          type: 'text',
          content: child.outerHTML
        });
      }
    });

      if (blockArray.length === 0) {
        blockArray.push({
          id: blockId++,
          type: 'text',
          content: '<p>Start typing your email content here...</p>'
        });
      }

      setBlocks(blockArray);
    } catch (error) {
      console.error('Error parsing HTML to blocks:', error);
      // Fallback to empty block
      setBlocks([{ id: Date.now(), type: 'text', content: '<p>Start typing your email content here...</p>' }]);
    }
  };

  const blocksToHTML = (blocksArray) => {
    // Wrap in email container with design settings
    const emailStyle = `
      width: ${settings.emailWidth}px;
      max-width: 100%;
      margin: 0 auto;
      background-color: ${settings.backgroundColor};
      border: ${settings.borderWidth}px solid ${settings.borderColor};
      font-family: ${settings.bodyFont};
      font-size: ${settings.bodyFontSize}px;
      line-height: ${settings.lineHeight};
      color: ${settings.bodyTextColor};
    `;

    const content = blocksArray.map(block => block.content).join('');
    
    return `
      <div style="${emailStyle}">
        ${settings.backgroundImage ? `<div style="background-image: url(${settings.backgroundImage}); background-size: cover; background-position: center; min-height: 100%;">${content}</div>` : content}
      </div>
    `;
  };

  const handleDragStart = (e, blockId) => {
    setDraggedBlock(blockId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e, targetBlockId) => {
    e.preventDefault();
    if (!draggedBlock || draggedBlock === targetBlockId) return;

    const draggedIndex = blocks.findIndex(b => b.id === draggedBlock);
    const targetIndex = blocks.findIndex(b => b.id === targetBlockId);

    if (draggedIndex === -1 || targetIndex === -1) return;

    const newBlocks = [...blocks];
    const [removed] = newBlocks.splice(draggedIndex, 1);
    newBlocks.splice(targetIndex, 0, removed);

    setBlocks(newBlocks);
    setDraggedBlock(null);
  };

  const handleDragEnd = () => {
    setDraggedBlock(null);
  };

  const addBlock = (type) => {
    let content = '';
    switch (type) {
      case 'header':
        content = '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; text-align: center; color: white;"><h1 style="margin: 0;">Header</h1></div>';
        break;
      case 'text':
        content = '<p style="margin: 10px 0;">New paragraph</p>';
        break;
      case 'heading':
        content = `<h2 style="font-size: 24px; font-weight: bold; margin: 20px 0 10px 0; color: ${settings.bodyTextColor};">Heading</h2>`;
        break;
      case 'image':
        content = '<div style="text-align: center; margin: 20px 0;"><img src="https://via.placeholder.com/400x200" alt="Image" style="max-width: 100%; height: auto;" /></div>';
        break;
      case 'button':
        content = '<div style="text-align: center; margin: 20px 0;"><a href="#" style="display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 6px;">Button Text</a></div>';
        break;
      case 'divider':
        content = '<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;" />';
        break;
      case 'spacer':
        content = '<div style="height: 20px;"></div>';
        break;
      case 'two-column':
        content = `
          <table style="width: 100%; margin: 20px 0; border-collapse: collapse;">
            <tr>
              <td style="width: 50%; padding: 10px; vertical-align: top;">
                <p>Left column content</p>
              </td>
              <td style="width: 50%; padding: 10px; vertical-align: top;">
                <p>Right column content</p>
              </td>
            </tr>
          </table>
        `;
        break;
      case 'footer':
        content = '<div style="background: #f3f4f6; padding: 20px; text-align: center; margin-top: 20px;"><p style="margin: 5px 0; color: #6b7280;">Footer content</p></div>';
        break;
      default:
        return;
    }

    const newBlock = {
      id: Date.now(),
      type: type,
      content: content
    };

    setBlocks([...blocks, newBlock]);
  };

  const updateBlockContent = (blockId, newContent) => {
    setBlocks(blocks.map(block =>
      block.id === blockId ? { ...block, content: newContent } : block
    ));
  };

  const deleteBlock = (blockId) => {
    setBlocks(blocks.filter(block => block.id !== blockId));
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await fetch('/api/communication/email/upload-image', {
        method: 'POST',
        credentials: 'include',
        body: formData
      });

      const data = await response.json();
      if (data.success) {
        // Use the image URL from API (already includes /api/communication/uploads/...)
        const imageUrl = data.image_url;
        const imgStyle = imageType === 'header' 
          ? `width: 100%; max-width: ${settings.emailWidth}px; height: auto; display: block; margin: 0 auto;`
          : 'max-width: 100%; height: auto;';
        
        const imgTag = imageType === 'header'
          ? `<img src="${imageUrl}" alt="Header image" style="${imgStyle}" data-type="header" />`
          : `<div style="text-align: center; margin: 20px 0;"><img src="${imageUrl}" alt="Image" style="${imgStyle}" /></div>`;
        
        const newBlock = {
          id: Date.now(),
          type: imageType === 'header' ? 'header-image' : 'image',
          content: imgTag
        };

        if (imageType === 'header') {
          const filteredBlocks = blocks.filter(b => b.type !== 'header-image');
          setBlocks([newBlock, ...filteredBlocks]);
        } else {
          setBlocks([...blocks, newBlock]);
        }

        setShowImageDialog(false);
        setImageType('regular');
      } else {
        alert('Failed to upload image: ' + data.error);
      }
    } catch (error) {
      console.error('Error uploading image:', error);
      alert('Error uploading image');
    }
  };

  const handleInsertVideo = () => {
    if (videoUrl) {
      let embedHtml = '';
      
      if (videoUrl.includes('youtube.com/watch') || videoUrl.includes('youtu.be')) {
        const videoId = videoUrl.includes('youtu.be') 
          ? videoUrl.split('youtu.be/')[1].split('?')[0]
          : videoUrl.split('v=')[1].split('&')[0];
        embedHtml = `<div style="margin: 20px 0; text-align: center;">
          <iframe width="560" height="315" src="https://www.youtube.com/embed/${videoId}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="max-width: 100%; height: auto;"></iframe>
        </div>`;
      } else if (videoUrl.includes('vimeo.com')) {
        const videoId = videoUrl.split('vimeo.com/')[1].split('?')[0];
        embedHtml = `<div style="margin: 20px 0; text-align: center;">
          <iframe src="https://player.vimeo.com/video/${videoId}" width="560" height="315" frameborder="0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen style="max-width: 100%; height: auto;"></iframe>
        </div>`;
      } else {
        embedHtml = `<div style="margin: 20px 0; text-align: center;">
          <a href="${videoUrl}" target="_blank" style="display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 6px;">
            Watch Video
          </a>
        </div>`;
      }
      
      const newBlock = {
        id: Date.now(),
        type: 'video',
        content: embedHtml
      };

      setBlocks([...blocks, newBlock]);
      setShowVideoDialog(false);
      setVideoUrl('');
    }
  };

  const handleTextInput = (blockId, e) => {
    // Fix backwards text - maintain proper text direction
    try {
      const element = e.target;
      
      // Safe check for selection API (may not be available on all mobile browsers)
      if (typeof window === 'undefined' || !window.getSelection) {
        updateBlockContent(blockId, element.innerHTML);
        return;
      }
      
      const selection = window.getSelection();
      if (!selection || selection.rangeCount === 0) {
        updateBlockContent(blockId, element.innerHTML);
        return;
      }
      
      const range = selection.getRangeAt(0);
      const cursorPos = range.startOffset;
      
      // Update content
      updateBlockContent(blockId, element.innerHTML);
      
      // Restore cursor position
      requestAnimationFrame(() => {
        try {
          if (typeof document === 'undefined' || !document.createRange) {
            return;
          }
          
          const textNode = element.childNodes[0] || element;
          if (textNode && textNode.nodeType === Node.TEXT_NODE) {
            const maxOffset = textNode.textContent ? textNode.textContent.length : 0;
            const safeOffset = Math.min(cursorPos, maxOffset);
            const newRange = document.createRange();
            newRange.setStart(textNode, safeOffset);
            newRange.setEnd(textNode, safeOffset);
            selection.removeAllRanges();
            selection.addRange(newRange);
          }
        } catch (err) {
          // Ignore cursor restoration errors - not critical
          console.debug('Cursor restoration failed:', err);
        }
      });
    } catch (error) {
      // Fallback: just update content without cursor restoration
      console.debug('Text input error:', error);
      updateBlockContent(blockId, e.target.innerHTML);
    }
  };

  return (
    <div className="flex flex-col md:flex-row h-full">
      {/* Content Blocks Sidebar */}
      <div className="w-full md:w-64 bg-slate-800 border-r border-white/10 p-2 md:p-4 overflow-y-auto flex-shrink-0">
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-white font-semibold text-sm">Content</span>
            <span className="text-white/40 text-xs">Design</span>
          </div>
        </div>
        
        <div className="grid grid-cols-4 md:grid-cols-2 gap-2">
          <button
            onClick={() => addBlock('header')}
            className="flex flex-col items-center gap-2 p-3 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
            title="Header"
          >
            <Bars3Icon className="w-6 h-6 text-white/60" />
            <span className="text-white/60 text-xs">Header</span>
          </button>
          
          <button
            onClick={() => addBlock('text')}
            className="flex flex-col items-center gap-2 p-3 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
            title="Text"
          >
            <DocumentTextIcon className="w-6 h-6 text-white/60" />
            <span className="text-white/60 text-xs">Text</span>
          </button>
          
          <button
            onClick={() => {
              setImageType('regular');
              fileInputRef.current?.click();
            }}
            className="flex flex-col items-center gap-2 p-3 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
            title="Image"
          >
            <PhotoIcon className="w-6 h-6 text-white/60" />
            <span className="text-white/60 text-xs">Image</span>
          </button>
          
          <button
            onClick={() => setShowVideoDialog(true)}
            className="flex flex-col items-center gap-2 p-3 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
            title="Video"
          >
            <PlayIcon className="w-6 h-6 text-white/60" />
            <span className="text-white/60 text-xs">Video</span>
          </button>
          
          <button
            onClick={() => addBlock('button')}
            className="flex flex-col items-center gap-2 p-3 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
            title="Button"
          >
            <Squares2X2Icon className="w-6 h-6 text-white/60" />
            <span className="text-white/60 text-xs">Button</span>
          </button>
          
          <button
            onClick={() => addBlock('divider')}
            className="flex flex-col items-center gap-2 p-3 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
            title="Divider"
          >
            <MinusIcon className="w-6 h-6 text-white/60" />
            <span className="text-white/60 text-xs">Divider</span>
          </button>
          
          <button
            onClick={() => addBlock('spacer')}
            className="flex flex-col items-center gap-2 p-3 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
            title="Spacer"
          >
            <RectangleStackIcon className="w-6 h-6 text-white/60" />
            <span className="text-white/60 text-xs">Spacer</span>
          </button>
          
          <button
            onClick={() => addBlock('footer')}
            className="flex flex-col items-center gap-2 p-3 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
            title="Footer"
          >
            <Bars3Icon className="w-6 h-6 text-white/60" />
            <span className="text-white/60 text-xs">Footer</span>
          </button>
        </div>
      </div>

      {/* Main Editor Area */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        {/* Toolbar */}
        <div className="bg-slate-700 border-b border-white/10 p-2 flex items-center gap-2 flex-shrink-0 overflow-x-auto">
          <button className="p-2 hover:bg-white/10 rounded text-white/60 flex-shrink-0" title="Undo">
            ↶
          </button>
          <button className="p-2 hover:bg-white/10 rounded text-white/60 flex-shrink-0" title="Redo">
            ↷
          </button>
          <div className="flex-1"></div>
          <button
            onClick={() => {
              setImageType('header');
              headerImageInputRef.current?.click();
            }}
            className="px-3 py-1 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 rounded text-sm whitespace-nowrap flex-shrink-0"
            title="Add Header Image"
          >
            Add Header Image
          </button>
        </div>

        {/* Email Preview/Editor */}
        <div className="flex-1 overflow-y-auto overflow-x-auto bg-slate-600 p-2 md:p-8">
          <div className="max-w-4xl mx-auto relative">
            <div 
              style={{
                width: `${settings.emailWidth}px`,
                maxWidth: '100%',
                margin: '0 auto',
                backgroundColor: settings.backgroundColor,
                border: `${settings.borderWidth}px solid ${settings.borderColor}`,
                minHeight: '400px',
                position: 'relative'
              }}
              className="bg-white shadow-lg"
            >
              {blocks.map((block, index) => (
                <div
                  key={block.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, block.id)}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, block.id)}
                  onDragEnd={handleDragEnd}
                  onClick={() => setSelectedBlock(block.id)}
                  className={`group relative border-2 border-transparent hover:border-blue-500/50 transition-all cursor-move ${
                    selectedBlock === block.id ? 'border-blue-500' : ''
                  } ${draggedBlock === block.id ? 'opacity-50' : ''}`}
                >
                  {/* Drag Handle - positioned inside to avoid overflow */}
                  <div className="absolute left-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    <Bars3Icon className="w-5 h-5 text-blue-500 bg-white/90 rounded p-1 shadow-md" />
                  </div>

                  {/* Block Content */}
                  <div className="p-4 pr-12">
                    {block.type === 'text' ? (
                      <div
                        ref={el => textBlockRefs.current[block.id] = el}
                        contentEditable
                        suppressContentEditableWarning
                        onInput={(e) => handleTextInput(block.id, e)}
                        onBlur={(e) => updateBlockContent(block.id, e.target.innerHTML)}
                        className="min-h-[50px] focus:outline-none"
                        style={{
                          direction: 'ltr',
                          unicodeBidi: 'embed',
                          fontFamily: settings.bodyFont,
                          fontSize: `${settings.bodyFontSize}px`,
                          lineHeight: settings.lineHeight,
                          color: settings.bodyTextColor
                        }}
                        dangerouslySetInnerHTML={{ __html: block.content }}
                      />
                    ) : (
                      <div dangerouslySetInnerHTML={{ __html: block.content }} />
                    )}
                  </div>

                  {/* Delete Button - positioned inside to avoid overflow */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteBlock(block.id);
                    }}
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 bg-red-500 hover:bg-red-600 rounded shadow-md z-10"
                    title="Delete block"
                  >
                    <TrashIcon className="w-4 h-4 text-white" />
                  </button>
                </div>
              ))}

              {blocks.length === 0 && (
                <div className="text-center py-12 text-gray-400">
                  Drag content blocks from the sidebar to start building your email
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Hidden file inputs */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleImageUpload}
        className="hidden"
      />
      <input
        ref={headerImageInputRef}
        type="file"
        accept="image/*"
        onChange={handleImageUpload}
        className="hidden"
      />

      {/* Video Dialog */}
      {showVideoDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="bg-slate-800 rounded-xl p-6 border border-white/10 max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">Insert Video</h3>
              <button
                onClick={() => setShowVideoDialog(false)}
                className="p-2 hover:bg-white/10 rounded transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-white" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-white/80 text-sm font-semibold mb-2">Video URL</label>
                <input
                  type="url"
                  value={videoUrl}
                  onChange={(e) => setVideoUrl(e.target.value)}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="YouTube, Vimeo, or direct video URL"
                />
              </div>
              <div className="flex items-center justify-end gap-3">
                <button
                  onClick={() => setShowVideoDialog(false)}
                  className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleInsertVideo}
                  disabled={!videoUrl}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  Insert
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Vision6EmailEditor;

