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
// Note: Bold, Italic, Underline icons may not exist in heroicons, using SVG instead

const Vision6EmailEditor = ({ value, onChange, designSettings, onDesignSettingsChange, onSelectionChange, onFormatHandlerChange }) => {
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
  const [showFormatToolbar, setShowFormatToolbar] = useState(false);
  const [toolbarPosition, setToolbarPosition] = useState({ top: 0, left: 0 });
  const [activeBlockId, setActiveBlockId] = useState(null);
  const fileInputRef = useRef(null);
  const headerImageInputRef = useRef(null);
  const textBlockRefs = useRef({});
  const selectionRangeRef = useRef(null);
  const caretPositionsRef = useRef({});
  const getCaretOffset = (element) => {
    if (typeof window === 'undefined' || !window.getSelection) return null;
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) return null;
    const range = selection.getRangeAt(0);
    if (!element.contains(range.startContainer)) return null;

    const preRange = range.cloneRange();
    preRange.selectNodeContents(element);
    preRange.setEnd(range.startContainer, range.startOffset);
    const offset = preRange.toString().length;
    return offset;
  };

  const setCaretOffset = (element, offset) => {
    if (typeof window === 'undefined' || !window.getSelection) return;
    const selection = window.getSelection();
    const range = document.createRange();

    let currentOffset = 0;
    const traverse = (node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        const textLength = node.textContent?.length || 0;
        if (currentOffset + textLength >= offset) {
          const newOffset = offset - currentOffset;
          range.setStart(node, newOffset);
          range.collapse(true);
          selection.removeAllRanges();
          selection.addRange(range);
          return true;
        }
        currentOffset += textLength;
      } else {
        for (let i = 0; i < node.childNodes.length; i++) {
          if (traverse(node.childNodes[i])) {
            return true;
          }
        }
      }
      return false;
    };

    traverse(element);
  };

  // Available fonts for the editor
  const availableFonts = [
    { name: 'Arial', value: 'Arial, sans-serif' },
    { name: 'Helvetica', value: 'Helvetica, Arial, sans-serif' },
    { name: 'Times New Roman', value: 'Times New Roman, serif' },
    { name: 'Georgia', value: 'Georgia, serif' },
    { name: 'Verdana', value: 'Verdana, sans-serif' },
    { name: 'Roboto', value: 'Roboto, sans-serif' },
    { name: 'Open Sans', value: 'Open Sans, sans-serif' },
    { name: 'Lato', value: 'Lato, sans-serif' },
    { name: 'Montserrat', value: 'Montserrat, sans-serif' },
    { name: 'Poppins', value: 'Poppins, sans-serif' },
    { name: 'Playfair Display', value: 'Playfair Display, serif' },
    { name: 'Merriweather', value: 'Merriweather, serif' },
    { name: 'Source Sans Pro', value: 'Source Sans Pro, sans-serif' },
    { name: 'Raleway', value: 'Raleway, sans-serif' },
    { name: 'Oswald', value: 'Oswald, sans-serif' },
    { name: 'Lora', value: 'Lora, serif' },
    { name: 'PT Serif', value: 'PT Serif, serif' },
    { name: 'Crimson Text', value: 'Crimson Text, serif' },
    { name: 'Libre Baskerville', value: 'Libre Baskerville, serif' }
  ];

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

  useEffect(() => {
    if (activeBlockId && caretPositionsRef.current[activeBlockId] != null) {
      const element = textBlockRefs.current[activeBlockId];
      if (element) {
        requestAnimationFrame(() => {
          setCaretOffset(element, caretPositionsRef.current[activeBlockId]);
        });
      }
    }
  }, [blocks, activeBlockId]);

  useEffect(() => {
    if (activeBlockId && caretPositionsRef.current[activeBlockId] != null) {
      const element = textBlockRefs.current[activeBlockId];
      if (element) {
        requestAnimationFrame(() => {
          setCaretOffset(element, caretPositionsRef.current[activeBlockId]);
        });
      }
    }
  }, [blocks, activeBlockId]);

  // Global selection change listener to catch all selection changes
  useEffect(() => {
    const handleGlobalSelectionChange = () => {
      // Check if selection is within any of our text blocks
      const selection = window.getSelection();
      if (selection && selection.rangeCount > 0 && !selection.isCollapsed) {
        const range = selection.getRangeAt(0);
        const container = range.commonAncestorContainer;
        const element = container.nodeType === Node.TEXT_NODE 
          ? container.parentElement 
          : container;
        
        // Find which block this element belongs to
        for (const [blockId, ref] of Object.entries(textBlockRefs.current)) {
          if (ref && (ref === element || ref.contains(element))) {
            // Call handleSelectionChange logic inline to avoid dependency issues
            const selectedText = selection.toString().trim();
            if (selectedText.length > 0) {
              setActiveBlockId(blockId);
              
              const rect = range.getBoundingClientRect();
              const toolbarWidth = 320;
              const toolbarHeight = 50;
              const padding = 10;
              
              let top = rect.top - toolbarHeight - padding;
              let left = rect.left + (rect.width / 2);
              
              if (top < padding) {
                top = rect.bottom + padding;
              }
              if (left < toolbarWidth / 2) {
                left = toolbarWidth / 2;
              }
              if (left > window.innerWidth - toolbarWidth / 2) {
                left = window.innerWidth - toolbarWidth / 2;
              }
              
              setToolbarPosition({
                top: Math.max(padding, top),
                left: left
              });
              
              setShowFormatToolbar(true);
            }
            break;
          }
        }
      }
    };

    document.addEventListener('selectionchange', handleGlobalSelectionChange);
    return () => {
      document.removeEventListener('selectionchange', handleGlobalSelectionChange);
    };
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
      } else if (['H1', 'H2', 'H3', 'H4', 'H5', 'H6'].includes(child.tagName)) {
        blockArray.push({
          id: blockId++,
          type: 'heading',
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

  // Formatting functions
  const execCommand = (command, value = null) => {
    // Save current selection
    const selection = window.getSelection();
    let savedRange = null;
    if (selection && selection.rangeCount > 0) {
      savedRange = selection.getRangeAt(0).cloneRange();
    }
    
    document.execCommand(command, false, value);
    
    // Restore selection and keep toolbar visible
    if (savedRange && activeBlockId && textBlockRefs.current[activeBlockId]) {
      const element = textBlockRefs.current[activeBlockId];
      element.focus();
      
      // Restore selection
      try {
        selection.removeAllRanges();
        selection.addRange(savedRange);
      } catch (e) {
        // If selection can't be restored, just keep focus
      }
      
      // Force LTR after formatting
      element.setAttribute('dir', 'ltr');
      element.style.direction = 'ltr';
      element.style.unicodeBidi = 'embed';
      element.style.textAlign = 'left';
      element.style.writingMode = 'horizontal-tb';
      
      // Update the block content after formatting
      updateBlockContent(activeBlockId, element.innerHTML);
      
      // Keep toolbar visible
      setTimeout(() => {
        handleSelectionChange(activeBlockId);
      }, 50);
    }
  };

  const handleFormat = (command, value = null) => {
    if (activeBlockId && textBlockRefs.current[activeBlockId]) {
      const element = textBlockRefs.current[activeBlockId];
      
      // Save selection before focusing
      const selection = window.getSelection();
      let savedRange = null;
      if (selection && selection.rangeCount > 0 && !selection.isCollapsed) {
        savedRange = selection.getRangeAt(0).cloneRange();
      }
      
      element.focus();
      
      // Restore selection if we had one
      if (savedRange) {
        try {
          selection.removeAllRanges();
          selection.addRange(savedRange);
        } catch (e) {
          // Selection might be invalid, continue anyway
        }
      }
      
      execCommand(command, value);
    }
  };

  const applyExternalFormat = (command, value = null) => {
    if (!activeBlockId || !textBlockRefs.current[activeBlockId]) return;
    const element = textBlockRefs.current[activeBlockId];
    element.focus({ preventScroll: true });

    const selection = window.getSelection();
    if (selection) {
      selection.removeAllRanges();
      if (selectionRangeRef.current) {
        selection.addRange(selectionRangeRef.current);
      } else {
        const range = document.createRange();
        range.selectNodeContents(element);
        range.collapse(false);
        selection.addRange(range);
      }
    }

    document.execCommand(command, false, value);
    updateBlockContent(activeBlockId, element.innerHTML);

    if (selection && selection.rangeCount > 0) {
      selectionRangeRef.current = selection.getRangeAt(0).cloneRange();
    }
    handleSelectionChange(activeBlockId);
  };

  useEffect(() => {
    if (typeof onFormatHandlerChange === 'function') {
      onFormatHandlerChange(applyExternalFormat);
    }
  }, [applyExternalFormat, onFormatHandlerChange]);

  const handleSelectionChange = (blockId) => {
    if (typeof window === 'undefined' || !window.getSelection) return;
    
    const selection = window.getSelection();
    
    // Check if there's a selection with actual text
    const hasSelection = selection && 
                        selection.rangeCount > 0 && 
                        !selection.isCollapsed && 
                        selection.toString().trim().length > 0;
    
    if (hasSelection) {
      setActiveBlockId(blockId);
      
      // Position toolbar above selection using viewport coordinates (for fixed positioning)
      const range = selection.getRangeAt(0);
      selectionRangeRef.current = range.cloneRange();
      const rect = range.getBoundingClientRect();
      
      // Use viewport coordinates for fixed positioning
      const toolbarWidth = 320;
      const toolbarHeight = 50;
      const padding = 10;
      
      let top = rect.top - toolbarHeight - padding;
      let left = rect.left + (rect.width / 2);
      
      // Ensure toolbar stays within viewport
      if (top < padding) {
        top = rect.bottom + padding;
      }
      if (left < toolbarWidth / 2) {
        left = toolbarWidth / 2;
      }
      if (left > window.innerWidth - toolbarWidth / 2) {
        left = window.innerWidth - toolbarWidth / 2;
      }
      
      setToolbarPosition({
        top: Math.max(padding, top),
        left: left
      });
      
      // Show toolbar immediately (no delay for better UX)
      clearTimeout(window._toolbarTimeout);
      setShowFormatToolbar(true);
      
      // Notify parent component about selection
      if (onSelectionChange) {
        onSelectionChange(true);
      }
    } else {
      // Only hide if we're sure there's no selection
      clearTimeout(window._toolbarTimeout);
      window._toolbarTimeout = setTimeout(() => {
        // Double-check selection is still empty
        const currentSelection = window.getSelection();
        if (!currentSelection || 
            currentSelection.rangeCount === 0 || 
            currentSelection.isCollapsed || 
            currentSelection.toString().trim().length === 0) {
          setShowFormatToolbar(false);
          selectionRangeRef.current = null;
          
          // Notify parent component
          if (onSelectionChange) {
            onSelectionChange(false);
          }
        }
      }, 300);
    }
  };

  const handleTextInput = (blockId, e) => {
    const element = e.target;
    
    // IMMEDIATELY force LTR direction - don't wait for animation frame
    element.setAttribute('dir', 'ltr');
    element.style.direction = 'ltr';
    element.style.unicodeBidi = 'embed';
    element.style.textAlign = 'left';
    element.style.writingMode = 'horizontal-tb';
    
    // Check if text was inserted in wrong direction and fix it
    const selection = window.getSelection();
    if (selection && selection.rangeCount > 0) {
      const range = selection.getRangeAt(0);
      const textNode = range.startContainer;
      
      // If we have a text node, check its direction
      if (textNode && textNode.nodeType === Node.TEXT_NODE) {
        const parent = textNode.parentElement;
        if (parent) {
          parent.setAttribute('dir', 'ltr');
          parent.style.direction = 'ltr';
          parent.style.unicodeBidi = 'embed';
          parent.style.textAlign = 'left';
          parent.style.writingMode = 'horizontal-tb';
        }
      }
    }
    
    // Fix all child elements too
    const allElements = element.querySelectorAll('*');
    allElements.forEach(el => {
      el.setAttribute('dir', 'ltr');
      el.style.direction = 'ltr';
      el.style.unicodeBidi = 'embed';
      el.style.textAlign = 'left';
      el.style.writingMode = 'horizontal-tb';
    });
    
    // Also force it in the next frame to catch any browser changes
    requestAnimationFrame(() => {
      element.setAttribute('dir', 'ltr');
      element.style.direction = 'ltr';
      element.style.unicodeBidi = 'embed';
      element.style.textAlign = 'left';
      element.style.writingMode = 'horizontal-tb';
      
      // Double-check all text nodes
      const walker = document.createTreeWalker(
        element,
        NodeFilter.SHOW_TEXT,
        null
      );
      let node;
      while (node = walker.nextNode()) {
        const parent = node.parentElement;
        if (parent) {
          parent.setAttribute('dir', 'ltr');
          parent.style.direction = 'ltr';
          parent.style.unicodeBidi = 'embed';
          parent.style.textAlign = 'left';
          parent.style.writingMode = 'horizontal-tb';
        }
      }
    });
    
    // Store caret position before updating content (to restore after re-render)
    const caretOffset = getCaretOffset(element);
    if (caretOffset !== null) {
      caretPositionsRef.current[blockId] = caretOffset;
    }

    // Update content (debounced to reduce clunkiness)
    clearTimeout(element._updateTimeout);
    element._updateTimeout = setTimeout(() => {
      updateBlockContent(blockId, element.innerHTML);
    }, 100);
    
    // Check for selection to show toolbar (debounced)
    clearTimeout(element._selectionTimeout);
    element._selectionTimeout = setTimeout(() => {
      handleSelectionChange(blockId);
    }, 200);
  };

  return (
    <div className="flex h-full bg-slate-700">
      {/* Global styles for better text editing */}
      <style>{`
        /* Force LTR direction globally for all contentEditable - ULTRA AGGRESSIVE */
        [contenteditable="true"],
        [contenteditable="true"] *,
        [contenteditable="true"] *::before,
        [contenteditable="true"] *::after {
          direction: ltr !important;
          unicode-bidi: embed !important;
          text-align: left !important;
          writing-mode: horizontal-tb !important;
          text-orientation: mixed !important;
        }
        /* Force LTR on the entire editor container */
        .email-editor-container,
        .email-editor-container * {
          direction: ltr !important;
          unicode-bidi: embed !important;
        }
        [contenteditable="true"] {
          caret-color: #000000 !important;
        }
        [contenteditable="true"]:focus {
          direction: ltr !important;
          unicode-bidi: embed !important;
          text-align: left !important;
          writing-mode: horizontal-tb !important;
          caret-color: #000000 !important;
          background-color: rgba(59, 130, 246, 0.08) !important;
        }
        /* Better text selection visibility */
        [contenteditable="true"]::selection {
          background-color: rgba(59, 130, 246, 0.3) !important;
          color: inherit !important;
          direction: ltr !important;
        }
        [contenteditable="true"]::-moz-selection {
          background-color: rgba(59, 130, 246, 0.3) !important;
          color: inherit !important;
          direction: ltr !important;
        }
        /* Prevent RTL at the CSS level - ALL elements */
        [contenteditable="true"] span,
        [contenteditable="true"] div,
        [contenteditable="true"] p,
        [contenteditable="true"] h1,
        [contenteditable="true"] h2,
        [contenteditable="true"] h3,
        [contenteditable="true"] strong,
        [contenteditable="true"] em,
        [contenteditable="true"] u {
          direction: ltr !important;
          unicode-bidi: embed !important;
          writing-mode: horizontal-tb !important;
        }
        /* Fix select styling in toolbar */
        .format-toolbar select {
          color: #111827 !important;
          background-color: white !important;
        }
        .format-toolbar select option {
          color: #111827 !important;
          background-color: white !important;
        }
      `}</style>
      {/* Content Blocks Sidebar */}
      <div className="w-72 bg-slate-800 border-r border-white/10 p-4 overflow-y-auto flex-shrink-0">
        
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => addBlock('header')}
            className="flex flex-col items-center justify-center gap-2 p-4 bg-white/5 hover:bg-white/10 rounded-lg transition-all hover:scale-105 border border-white/5"
            title="Header"
          >
            <Bars3Icon className="w-7 h-7 text-white/70" />
            <span className="text-white/70 text-xs font-medium">Header</span>
          </button>
          
          <button
            onClick={() => addBlock('text')}
            className="flex flex-col items-center justify-center gap-2 p-4 bg-white/5 hover:bg-white/10 rounded-lg transition-all hover:scale-105 border border-white/5"
            title="Text"
          >
            <DocumentTextIcon className="w-7 h-7 text-white/70" />
            <span className="text-white/70 text-xs font-medium">Text</span>
          </button>
          
          <button
            onClick={() => {
              setImageType('regular');
              fileInputRef.current?.click();
            }}
            className="flex flex-col items-center justify-center gap-2 p-4 bg-white/5 hover:bg-white/10 rounded-lg transition-all hover:scale-105 border border-white/5"
            title="Image"
          >
            <PhotoIcon className="w-7 h-7 text-white/70" />
            <span className="text-white/70 text-xs font-medium">Image</span>
          </button>
          
          <button
            onClick={() => setShowVideoDialog(true)}
            className="flex flex-col items-center justify-center gap-2 p-4 bg-white/5 hover:bg-white/10 rounded-lg transition-all hover:scale-105 border border-white/5"
            title="Video"
          >
            <PlayIcon className="w-7 h-7 text-white/70" />
            <span className="text-white/70 text-xs font-medium">Video</span>
          </button>
          
          <button
            onClick={() => addBlock('button')}
            className="flex flex-col items-center justify-center gap-2 p-4 bg-white/5 hover:bg-white/10 rounded-lg transition-all hover:scale-105 border border-white/5"
            title="Button"
          >
            <Squares2X2Icon className="w-7 h-7 text-white/70" />
            <span className="text-white/70 text-xs font-medium">Button</span>
          </button>
          
          <button
            onClick={() => addBlock('divider')}
            className="flex flex-col items-center justify-center gap-2 p-4 bg-white/5 hover:bg-white/10 rounded-lg transition-all hover:scale-105 border border-white/5"
            title="Divider"
          >
            <MinusIcon className="w-7 h-7 text-white/70" />
            <span className="text-white/70 text-xs font-medium">Divider</span>
          </button>
          
          <button
            onClick={() => addBlock('spacer')}
            className="flex flex-col items-center justify-center gap-2 p-4 bg-white/5 hover:bg-white/10 rounded-lg transition-all hover:scale-105 border border-white/5"
            title="Spacer"
          >
            <RectangleStackIcon className="w-7 h-7 text-white/70" />
            <span className="text-white/70 text-xs font-medium">Spacer</span>
          </button>
          
          <button
            onClick={() => addBlock('footer')}
            className="flex flex-col items-center justify-center gap-2 p-4 bg-white/5 hover:bg-white/10 rounded-lg transition-all hover:scale-105 border border-white/5"
            title="Footer"
          >
            <Bars3Icon className="w-7 h-7 text-white/70" />
            <span className="text-white/70 text-xs font-medium">Footer</span>
          </button>
        </div>
      </div>

      {/* Main Editor Area */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden bg-slate-100">
        {/* Toolbar */}
        <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center gap-3 flex-shrink-0">
          <button className="p-1.5 hover:bg-gray-100 rounded text-gray-600 flex-shrink-0 transition-colors" title="Undo">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
          </button>
          <button className="p-1.5 hover:bg-gray-100 rounded text-gray-600 flex-shrink-0 transition-colors" title="Redo">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 10h-10a8 8 0 00-8 8v2M21 10l-6 6m6-6l-6-6" />
            </svg>
          </button>
          <div className="flex-1"></div>
          <button
            onClick={() => {
              setImageType('header');
              headerImageInputRef.current?.click();
            }}
            className="px-4 py-1.5 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm whitespace-nowrap flex-shrink-0 transition-colors font-medium"
            title="Add Header Image"
          >
            Add Header Image
          </button>
        </div>

        {/* Email Preview/Editor */}
        <div className="flex-1 overflow-y-auto overflow-x-auto bg-slate-100 p-8 email-editor-container" dir="ltr" lang="en" style={{ direction: 'ltr', unicodeBidi: 'embed' }}>
          <div className="max-w-5xl mx-auto relative">
            <div 
              style={{
                width: `${settings.emailWidth}px`,
                maxWidth: '100%',
                margin: '0 auto',
                backgroundColor: settings.backgroundColor,
                border: `${settings.borderWidth}px solid ${settings.borderColor}`,
                minHeight: '500px',
                position: 'relative',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
              }}
              className="bg-white"
            >
              {blocks.map((block, index) => (
                <div
                  key={block.id}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, block.id)}
                  onClick={() => setSelectedBlock(block.id)}
                  className={`group relative border-2 border-transparent hover:border-blue-500/50 transition-all ${
                    selectedBlock === block.id ? 'border-blue-500' : ''
                  } ${draggedBlock === block.id ? 'opacity-50' : ''}`}
                >
                  {/* Drag Handle - only this is draggable, not the whole block */}
                  <div 
                    className="absolute left-3 top-3 opacity-0 group-hover:opacity-100 transition-opacity z-10"
                    draggable
                    onDragStart={(e) => {
                      e.stopPropagation();
                      handleDragStart(e, block.id);
                    }}
                    onDragEnd={handleDragEnd}
                    onMouseDown={(e) => {
                      // Prevent text selection when starting drag
                      e.stopPropagation();
                    }}
                    style={{ cursor: 'grab' }}
                  >
                    <div className="bg-blue-500 text-white rounded p-1.5 shadow-lg cursor-grab active:cursor-grabbing">
                      <Bars3Icon className="w-4 h-4" />
                    </div>
                  </div>

                  {/* Block Content */}
                  <div className="p-6 pr-14">
                    {block.type === 'text' || block.type === 'heading' ? (
                      <div
                        ref={el => {
                          textBlockRefs.current[block.id] = el;
                          // Force LTR direction on mount and update
                          if (el) {
                            // IMMEDIATE aggressive LTR enforcement
                            const forceLTR = () => {
                              el.setAttribute('dir', 'ltr');
                              el.style.direction = 'ltr';
                              el.style.unicodeBidi = 'embed';
                              el.style.textAlign = 'left';
                              el.style.writingMode = 'horizontal-tb';
                              
                              // Force LTR on ALL descendants
                              const allNodes = el.querySelectorAll('*');
                              allNodes.forEach(node => {
                                node.setAttribute('dir', 'ltr');
                                node.style.direction = 'ltr';
                                node.style.unicodeBidi = 'embed';
                                node.style.textAlign = 'left';
                                node.style.writingMode = 'horizontal-tb';
                              });
                              
                              // Check computed style and override if needed
                              const computed = window.getComputedStyle(el);
                              if (computed.direction !== 'ltr') {
                                el.style.setProperty('direction', 'ltr', 'important');
                              }
                            };
                            
                            forceLTR();
                            
                            // Watch for ANY changes - text, attributes, child nodes
                            const observer = new MutationObserver((mutations) => {
                              let needsFix = false;
                              
                              mutations.forEach(mutation => {
                                // Check if direction attribute changed
                                if (mutation.type === 'attributes' && 
                                    (mutation.attributeName === 'dir' || mutation.attributeName === 'style')) {
                                  if (el.getAttribute('dir') !== 'ltr' || 
                                      el.style.direction !== 'ltr') {
                                    needsFix = true;
                                  }
                                }
                                
                                // Check if text was added/changed
                                if (mutation.type === 'childList' || mutation.type === 'characterData') {
                                  needsFix = true;
                                }
                              });
                              
                              if (needsFix) {
                                // Use requestAnimationFrame for immediate fix
                                requestAnimationFrame(() => {
                                  forceLTR();
                                  
                                  // Also check all text nodes
                                  const walker = document.createTreeWalker(
                                    el,
                                    NodeFilter.SHOW_TEXT,
                                    null
                                  );
                                  let textNode;
                                  while (textNode = walker.nextNode()) {
                                    const parent = textNode.parentElement;
                                    if (parent) {
                                      parent.setAttribute('dir', 'ltr');
                                      parent.style.direction = 'ltr';
                                      parent.style.unicodeBidi = 'embed';
                                      parent.style.textAlign = 'left';
                                      parent.style.writingMode = 'horizontal-tb';
                                    }
                                  }
                                });
                              }
                            });
                            
                            observer.observe(el, {
                              attributes: true,
                              attributeFilter: ['dir', 'style'],
                              childList: true,
                              subtree: true,
                              characterData: true
                            });
                            
                            // Also use a periodic check as backup
                            const intervalId = setInterval(() => {
                              const computed = window.getComputedStyle(el);
                              if (computed.direction !== 'ltr') {
                                forceLTR();
                              }
                            }, 100);
                            
                            // Clean up old observer/interval if they exist
                            if (el._directionObserver) {
                              el._directionObserver.disconnect();
                            }
                            if (el._directionInterval) {
                              clearInterval(el._directionInterval);
                            }
                            
                            // Store observer and interval for cleanup
                            el._directionObserver = observer;
                            el._directionInterval = intervalId;
                          }
                        }}
                        contentEditable
                        suppressContentEditableWarning
                        dir="ltr"
                        lang="en"
                        spellCheck="false"
                        autoCorrect="off"
                        autoCapitalize="off"
                        onBeforeInput={(e) => {
                          // Intercept before input to force LTR - PREVENT default if RTL detected
                          const target = e.target;
                          target.setAttribute('dir', 'ltr');
                          target.style.setProperty('direction', 'ltr', 'important');
                          target.style.setProperty('unicode-bidi', 'embed', 'important');
                          target.style.setProperty('text-align', 'left', 'important');
                          target.style.setProperty('writing-mode', 'horizontal-tb', 'important');
                          
                          // Check computed style BEFORE allowing input
                          const computed = window.getComputedStyle(target);
                          if (computed.direction !== 'ltr') {
                            e.preventDefault();
                            target.style.setProperty('direction', 'ltr', 'important');
                            // Re-insert the text manually with LTR
                            if (e.data) {
                              const selection = window.getSelection();
                              if (selection && selection.rangeCount > 0) {
                                const range = selection.getRangeAt(0);
                                const textNode = document.createTextNode(e.data);
                                range.deleteContents();
                                range.insertNode(textNode);
                                range.setStartAfter(textNode);
                                range.collapse(true);
                                selection.removeAllRanges();
                                selection.addRange(range);
                                
                                // Ensure parent is LTR
                                const parent = textNode.parentElement;
                                if (parent) {
                                  parent.setAttribute('dir', 'ltr');
                                  parent.style.setProperty('direction', 'ltr', 'important');
                                  parent.style.setProperty('unicode-bidi', 'embed', 'important');
                                }
                              }
                            }
                          }
                        }}
                        onCompositionStart={(e) => {
                          // Force LTR when IME starts
                          const target = e.target;
                          target.setAttribute('dir', 'ltr');
                          target.style.direction = 'ltr';
                          target.style.unicodeBidi = 'embed';
                          target.style.textAlign = 'left';
                        }}
                        onCompositionUpdate={(e) => {
                          // Force LTR during IME composition
                          const target = e.target;
                          target.setAttribute('dir', 'ltr');
                          target.style.direction = 'ltr';
                          target.style.unicodeBidi = 'embed';
                          target.style.textAlign = 'left';
                        }}
                        onPaste={(e) => {
                          // Intercept paste to ensure LTR
                          e.preventDefault();
                          const target = e.target;
                          const text = e.clipboardData.getData('text/plain');
                          
                          // Insert text with explicit LTR
                          const selection = window.getSelection();
                          if (selection && selection.rangeCount > 0) {
                            const range = selection.getRangeAt(0);
                            range.deleteContents();
                            
                            // Create a span with explicit LTR direction
                            const span = document.createElement('span');
                            span.setAttribute('dir', 'ltr');
                            span.style.direction = 'ltr';
                            span.style.unicodeBidi = 'embed';
                            span.textContent = text;
                            
                            range.insertNode(span);
                            range.setStartAfter(span);
                            range.collapse(true);
                            selection.removeAllRanges();
                            selection.addRange(range);
                            
                            // Force LTR on target
                            target.setAttribute('dir', 'ltr');
                            target.style.setProperty('direction', 'ltr', 'important');
                            target.style.setProperty('unicode-bidi', 'embed', 'important');
                            
                            // Update content
                            setTimeout(() => {
                              updateBlockContent(block.id, target.innerHTML);
                            }, 0);
                          }
                        }}
                        onInput={(e) => {
                          // Input should be minimal now since we're handling everything in onBeforeInput
                          // Just ensure LTR and update content
                          const target = e.target;
                          
                          // Force LTR
                          target.setAttribute('dir', 'ltr');
                          target.setAttribute('lang', 'en');
                          target.style.setProperty('direction', 'ltr', 'important');
                          target.style.setProperty('unicode-bidi', 'embed', 'important');
                          
                          // Update content
                          handleTextInput(block.id, e);
                        }}
                        onBlur={(e) => {
                          // Don't hide toolbar if clicking on toolbar buttons
                          const relatedTarget = e.relatedTarget;
                          if (relatedTarget && relatedTarget.closest('.format-toolbar')) {
                            return;
                          }
                          
                          updateBlockContent(block.id, e.target.innerHTML);
                          // Hide toolbar with delay to prevent flashing
                          setTimeout(() => {
                            // Double-check we're not focusing on toolbar
                            if (document.activeElement && !document.activeElement.closest('.format-toolbar')) {
                              setShowFormatToolbar(false);
                            }
                          }, 300);
                        }}
                        onFocus={(e) => {
                          setActiveBlockId(block.id);
                          // Ensure cursor is visible when focused
                          const textColor = settings.bodyTextColor || '#000000';
                          e.target.style.caretColor = textColor;
                          e.target.style.color = textColor;
                          // Aggressively force LTR
                          e.target.style.direction = 'ltr';
                          e.target.style.unicodeBidi = 'embed';
                          e.target.style.textAlign = 'left';
                          e.target.style.writingMode = 'horizontal-tb';
                          e.target.setAttribute('dir', 'ltr');
                          
                          // Use requestAnimationFrame to ensure it sticks
                          requestAnimationFrame(() => {
                            e.target.style.direction = 'ltr';
                            e.target.style.unicodeBidi = 'embed';
                            e.target.style.textAlign = 'left';
                            e.target.style.writingMode = 'horizontal-tb';
                            e.target.setAttribute('dir', 'ltr');
                          });
                        }}
                        onKeyDown={(e) => {
                          const target = e.target;
                          
                          // IMMEDIATELY force LTR before any key processing
                          target.setAttribute('dir', 'ltr');
                          target.setAttribute('lang', 'en');
                          target.style.setProperty('direction', 'ltr', 'important');
                          target.style.setProperty('unicode-bidi', 'embed', 'important');
                          target.style.setProperty('text-align', 'left', 'important');
                          target.style.setProperty('writing-mode', 'horizontal-tb', 'important');
                          
                          // Force all ancestors
                          let current = target.parentElement;
                          while (current) {
                            current.setAttribute('dir', 'ltr');
                            current.setAttribute('lang', 'en');
                            current.style.setProperty('direction', 'ltr', 'important');
                            current = current.parentElement;
                          }
                        }}
                        onMouseUp={(e) => {
                          // Check selection immediately and with a small delay
                          handleSelectionChange(block.id);
                          setTimeout(() => handleSelectionChange(block.id), 50);
                        }}
                        onKeyUp={(e) => {
                          // Check selection immediately and with a small delay
                          handleSelectionChange(block.id);
                          setTimeout(() => handleSelectionChange(block.id), 50);
                        }}
                        onSelect={(e) => {
                          // Also check on select event
                          handleSelectionChange(block.id);
                        }}
                        className="min-h-[50px] focus:outline-none rounded px-2 py-1 -mx-2 -my-1"
                        style={{
                          direction: 'ltr',
                          unicodeBidi: 'embed',
                          fontFamily: settings.bodyFont,
                          fontSize: block.type === 'heading' ? '24px' : `${settings.bodyFontSize}px`,
                          lineHeight: settings.lineHeight,
                          fontWeight: block.type === 'heading' ? 'bold' : 'normal',
                          color: settings.bodyTextColor || '#000000',
                          caretColor: settings.bodyTextColor || '#000000',
                          backgroundColor: 'transparent',
                          outline: 'none',
                          // Better text selection styling
                          WebkitUserSelect: 'text',
                          MozUserSelect: 'text',
                          msUserSelect: 'text',
                          userSelect: 'text',
                          // Ensure text is readable
                          textShadow: 'none',
                          // Better spacing for editing
                          padding: '6px 10px',
                          margin: '4px 0',
                          borderRadius: '4px',
                          transition: 'background-color 0.15s ease',
                          // Ensure minimum contrast
                          minHeight: '1.5em',
                          // Better cursor visibility
                          cursor: 'text'
                        }}
                        onMouseEnter={(e) => {
                          if (document.activeElement !== e.target) {
                            e.target.style.backgroundColor = 'rgba(59, 130, 246, 0.08)';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (document.activeElement !== e.target) {
                            e.target.style.backgroundColor = 'transparent';
                          }
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
                    className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity p-2 bg-red-500 hover:bg-red-600 rounded shadow-lg z-10"
                    title="Delete block"
                  >
                    <TrashIcon className="w-4 h-4 text-white" />
                  </button>
                </div>
              ))}

              {blocks.length === 0 && (
                <div className="text-center py-20 text-gray-400">
                  <div className="mb-4">
                    <svg className="w-16 h-16 mx-auto text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                  </div>
                  <p className="text-lg font-medium text-gray-500">Start building your email</p>
                  <p className="text-sm text-gray-400 mt-2">Drag content blocks from the sidebar to get started</p>
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

