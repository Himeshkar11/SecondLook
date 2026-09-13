import React, { useEffect, useState } from 'react';
import { getTenderDashboard } from '../../services/dashboardService.js';
import EvaluationStats from './EvaluationStats.jsx';
import BidderEvaluationTable from './BidderEvaluationTable.jsx';
import RequirementIssueSummary from './RequirementIssueSummary.jsx';

export default function TenderEvaluationDashboard({ tenderId, onOpenBidder }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => { let active = true; getTenderDashboard(tenderId).then((value) => active && setData(value)).catch((reason) => active && setError(reason)); return () => { active = false; }; }, [tenderId]);
  if (error) return <p role="alert">Unable to load evaluation dashboard.</p>;
  if (!data) return <p>Loading evaluation dashboard...</p>;
  return <div><header><h1>{data.tender.title}</h1><p>{data.tender.reference_number} · {data.tender.status}</p></header><EvaluationStats summary={data.summary} /><section><h2>Bidder evaluations</h2><BidderEvaluationTable bidders={data.bidders} onOpen={onOpenBidder} /></section><RequirementIssueSummary requirements={data.requirement_issues} /></div>;
}
