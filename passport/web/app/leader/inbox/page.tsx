'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { AssignmentRow } from '@/components/AssignmentRow';

export default function InboxPage() {
  const router = useRouter();
  const [assignments, setAssignments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');

  useEffect(() => {
    loadInbox();
  }, [statusFilter]);

  const loadInbox = async () => {
    try {
      const data = await api.inbox.getAll(statusFilter || undefined);
      setAssignments(data);
    } catch (error: any) {
      if (error.message.includes('Unauthorized')) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async (assignmentId: string) => {
    try {
      await api.complete.complete({
        assignment_id: assignmentId,
        outcome: 'IN_PROGRESS',
        evidence_json: {},
      });
      loadInbox();
    } catch (error: any) {
      alert(`Failed to start: ${error.message}`);
    }
  };

  const handleComplete = async (assignmentId: string) => {
    try {
      await api.complete.complete({
        assignment_id: assignmentId,
        outcome: 'COMPLETE',
        evidence_json: { attendance_tag: 'completed', note: 'Great work!' },
      });
      alert('Assignment completed and stamp awarded!');
      loadInbox();
    } catch (error: any) {
      alert(`Failed to complete: ${error.message}`);
    }
  };

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Inbox</h1>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md"
          >
            <option value="">All Status</option>
            <option value="NEW">New</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="COMPLETE">Complete</option>
          </select>
        </div>

        <div className="space-y-4">
          {assignments.length === 0 ? (
            <div className="bg-white p-8 rounded-lg shadow text-center text-gray-500">
              No assignments found
            </div>
          ) : (
            assignments.map((assignment) => (
              <AssignmentRow
                key={assignment.id}
                assignment={assignment}
                onStart={handleStart}
                onComplete={handleComplete}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}










