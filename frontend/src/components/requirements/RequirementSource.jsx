import React from 'react';
export default function RequirementSource({ requirement }) { return <div><div>Source document: {requirement.source_document_id || 'Not available'}</div><div>Page: {requirement.source_page ?? 'Not available'}</div><div>Section: {requirement.source_section || 'Not available'}</div><div>Text: {requirement.source_text || 'Not available'}</div></div>; }
