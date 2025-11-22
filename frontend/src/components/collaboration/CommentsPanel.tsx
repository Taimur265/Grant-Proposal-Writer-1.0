'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';

interface Comment {
  id: string;
  content: string;
  comment_type: string;
  status: string;
  author_id: string;
  author_name?: string;
  section_id?: string;
  highlighted_text?: string;
  created_at: string;
  updated_at: string;
  reply_count: number;
}

interface CommentsPanelProps {
  targetType: 'proposal' | 'document' | 'project';
  targetId: string;
}

const COMMENT_TYPES = [
  { value: 'general', label: 'General', color: 'bg-gray-100 text-gray-700' },
  { value: 'suggestion', label: 'Suggestion', color: 'bg-blue-100 text-blue-700' },
  { value: 'question', label: 'Question', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'revision', label: 'Revision Needed', color: 'bg-orange-100 text-orange-700' },
  { value: 'approval', label: 'Approved', color: 'bg-green-100 text-green-700' },
];

export function CommentsPanel({ targetType, targetId }: CommentsPanelProps) {
  const queryClient = useQueryClient();
  const [newComment, setNewComment] = useState('');
  const [commentType, setCommentType] = useState('general');
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState('');
  const [expandedComment, setExpandedComment] = useState<string | null>(null);

  const { data: commentsData, isLoading } = useQuery({
    queryKey: ['comments', targetType, targetId],
    queryFn: async () => {
      const response = await api.get(`/collaboration/comments/${targetType}/${targetId}`);
      return response.data;
    },
  });

  const { data: repliesData } = useQuery({
    queryKey: ['replies', expandedComment],
    queryFn: async () => {
      const response = await api.get(`/collaboration/comments/${expandedComment}/replies`);
      return response.data;
    },
    enabled: !!expandedComment,
  });

  const addCommentMutation = useMutation({
    mutationFn: async (data: { content: string; comment_type: string; parent_id?: string }) => {
      const response = await api.post('/collaboration/comments', {
        content: data.content,
        comment_type: data.comment_type,
        target_type: targetType,
        target_id: targetId,
        parent_id: data.parent_id,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', targetType, targetId] });
      setNewComment('');
      setReplyContent('');
      setReplyingTo(null);
    },
  });

  const updateCommentMutation = useMutation({
    mutationFn: async ({ commentId, status }: { commentId: string; status: string }) => {
      const response = await api.patch(`/collaboration/comments/${commentId}`, { status });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', targetType, targetId] });
    },
  });

  const handleSubmitComment = () => {
    if (!newComment.trim()) return;
    addCommentMutation.mutate({ content: newComment, comment_type: commentType });
  };

  const handleSubmitReply = (parentId: string) => {
    if (!replyContent.trim()) return;
    addCommentMutation.mutate({ content: replyContent, comment_type: 'general', parent_id: parentId });
  };

  const getTypeInfo = (type: string) => {
    return COMMENT_TYPES.find((t) => t.value === type) || COMMENT_TYPES[0];
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="bg-white rounded-lg border">
      {/* Header */}
      <div className="px-4 py-3 border-b">
        <h3 className="font-medium text-gray-900">Comments</h3>
        <p className="text-sm text-gray-500">
          {commentsData?.comments?.length || 0} comments
        </p>
      </div>

      {/* New comment form */}
      <div className="p-4 border-b">
        <textarea
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder="Add a comment..."
          className="w-full px-3 py-2 border rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          rows={3}
        />
        <div className="mt-3 flex items-center justify-between">
          <div className="flex gap-2">
            {COMMENT_TYPES.map((type) => (
              <button
                key={type.value}
                onClick={() => setCommentType(type.value)}
                className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                  commentType === type.value ? type.color : 'bg-gray-50 text-gray-500 hover:bg-gray-100'
                }`}
              >
                {type.label}
              </button>
            ))}
          </div>
          <Button
            size="sm"
            onClick={handleSubmitComment}
            disabled={!newComment.trim() || addCommentMutation.isPending}
          >
            {addCommentMutation.isPending ? 'Posting...' : 'Post'}
          </Button>
        </div>
      </div>

      {/* Comments list */}
      <div className="divide-y max-h-[500px] overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-gray-500">Loading comments...</div>
        ) : commentsData?.comments?.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p>No comments yet</p>
            <p className="text-sm">Be the first to leave a comment</p>
          </div>
        ) : (
          commentsData?.comments?.map((comment: Comment) => (
            <div key={comment.id} className="p-4">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-medium">
                  {(comment.author_name || 'U')[0].toUpperCase()}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-gray-900 text-sm">
                      {comment.author_name || 'User'}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${getTypeInfo(comment.comment_type).color}`}>
                      {getTypeInfo(comment.comment_type).label}
                    </span>
                    <span className="text-xs text-gray-400">{formatDate(comment.created_at)}</span>
                  </div>

                  {comment.highlighted_text && (
                    <div className="mb-2 pl-3 border-l-2 border-yellow-400 bg-yellow-50 py-1 px-2 rounded-r text-sm text-gray-600 italic">
                      "{comment.highlighted_text}"
                    </div>
                  )}

                  <p className="text-gray-700 text-sm">{comment.content}</p>

                  <div className="mt-2 flex items-center gap-4 text-sm">
                    <button
                      onClick={() => setReplyingTo(replyingTo === comment.id ? null : comment.id)}
                      className="text-gray-500 hover:text-blue-600"
                    >
                      Reply
                    </button>
                    {comment.reply_count > 0 && (
                      <button
                        onClick={() => setExpandedComment(expandedComment === comment.id ? null : comment.id)}
                        className="text-blue-600 hover:text-blue-700"
                      >
                        {expandedComment === comment.id ? 'Hide' : 'View'} {comment.reply_count} {comment.reply_count === 1 ? 'reply' : 'replies'}
                      </button>
                    )}
                    {comment.status === 'open' && (
                      <button
                        onClick={() => updateCommentMutation.mutate({ commentId: comment.id, status: 'resolved' })}
                        className="text-gray-500 hover:text-green-600"
                      >
                        Resolve
                      </button>
                    )}
                    {comment.status === 'resolved' && (
                      <span className="text-green-600 text-xs">Resolved</span>
                    )}
                  </div>

                  {/* Reply form */}
                  {replyingTo === comment.id && (
                    <div className="mt-3 pl-4 border-l-2 border-gray-200">
                      <textarea
                        value={replyContent}
                        onChange={(e) => setReplyContent(e.target.value)}
                        placeholder="Write a reply..."
                        className="w-full px-3 py-2 border rounded-lg resize-none text-sm"
                        rows={2}
                      />
                      <div className="mt-2 flex gap-2">
                        <Button size="sm" onClick={() => handleSubmitReply(comment.id)}>
                          Reply
                        </Button>
                        <Button size="sm" variant="secondary" onClick={() => setReplyingTo(null)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Replies */}
                  {expandedComment === comment.id && repliesData?.replies && (
                    <div className="mt-3 pl-4 border-l-2 border-gray-200 space-y-3">
                      {repliesData.replies.map((reply: Comment) => (
                        <div key={reply.id} className="flex items-start gap-2">
                          <div className="w-6 h-6 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center text-xs font-medium">
                            U
                          </div>
                          <div>
                            <div className="flex items-center gap-2 mb-0.5">
                              <span className="font-medium text-gray-900 text-xs">User</span>
                              <span className="text-xs text-gray-400">{formatDate(reply.created_at)}</span>
                            </div>
                            <p className="text-gray-700 text-sm">{reply.content}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
