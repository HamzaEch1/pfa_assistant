import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import MermaidDiagram from './MermaidDiagram';

const Message = ({ message }) => {
  const extractMermaidDiagram = (content) => {
    const mermaidRegex = /```mermaid\n([\s\S]*?)```/;
    const match = content.match(mermaidRegex);
    if (match) {
      return {
        diagram: match[1].trim(),
        text: content.replace(match[0], '').trim()
      };
    }
    return { text: content };
  };

  const { text, diagram } = extractMermaidDiagram(message.content);

  return (
    <div className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'} p-4 rounded-lg mb-4`}>
      <div className="message-content">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeSanitize]}
          className="prose max-w-none"
        >
          {text}
        </ReactMarkdown>
        {diagram && <MermaidDiagram chart={diagram} />}
      </div>
    </div>
  );
};

export default Message; 