import React from 'react';
export default function RequirementReviewPanel({ requirement }) { return requirement ? <aside><h2>Review requirement</h2><p>{requirement.title}</p><p>Approval is an explicit officer action.</p></aside> : null; }
