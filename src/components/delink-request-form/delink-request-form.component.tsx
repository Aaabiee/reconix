'use client';

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { delinkService } from '@/services/delink.service';
import './delink-request-form.component.scss';

const delinkRequestSchema = z.object({
  recycledSimId: z.string().min(1, 'Recycled SIM is required'),
  delinkReason: z.string().min(10, 'Reason must be at least 10 characters'),
});

type DelinkRequestFormData = z.infer<typeof delinkRequestSchema>;

interface DelinkRequestFormProps {
  recycledSimId?: string;
  onSuccess?: () => void;
}

export const DelinkRequestForm: React.FC<DelinkRequestFormProps> = ({ recycledSimId, onSuccess }) => {
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [submitError, setSubmitError] = React.useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<DelinkRequestFormData>({
    resolver: zodResolver(delinkRequestSchema),
    defaultValues: {
      recycledSimId,
    },
  });

  const onSubmit = async (data: DelinkRequestFormData): Promise<void> => {
    setIsSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(false);

    try {
      await delinkService.createDelinkRequest(data.recycledSimId, data.delinkReason);
      setSubmitSuccess(true);
      onSuccess?.();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create delink request';
      setSubmitError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="delink-request-form space-y-4" noValidate>
      {submitError && (
        <div className="p-4 bg-error-50 border border-error-200 rounded-lg text-error-800 text-sm" role="alert">
          {submitError}
        </div>
      )}

      {submitSuccess && (
        <div className="p-4 bg-success-50 border border-success-200 rounded-lg text-success-800 text-sm" role="status">
          Delink request created successfully
        </div>
      )}

      <div>
        <label htmlFor="recycledSimId" className="block text-sm font-medium text-default mb-1">
          Recycled SIM
        </label>
        <input
          id="recycledSimId"
          type="text"
          placeholder="Enter recycled SIM ID"
          className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
            errors.recycledSimId ? 'border-error-500' : 'border-secondary-200'
          }`}
          {...register('recycledSimId')}
          aria-invalid={errors.recycledSimId ? 'true' : 'false'}
          disabled={!!recycledSimId}
        />
        {errors.recycledSimId && (
          <p className="text-error-600 text-sm mt-1">{errors.recycledSimId.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="delinkReason" className="block text-sm font-medium text-default mb-1">
          Reason for Delinking
        </label>
        <textarea
          id="delinkReason"
          placeholder="Explain why this SIM should be delinked"
          rows={4}
          className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
            errors.delinkReason ? 'border-error-500' : 'border-secondary-200'
          }`}
          {...register('delinkReason')}
          aria-invalid={errors.delinkReason ? 'true' : 'false'}
        />
        {errors.delinkReason && (
          <p className="text-error-600 text-sm mt-1">{errors.delinkReason.message}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full px-4 py-2 bg-primary-500 text-surface rounded-lg hover:bg-primary-600 disabled:opacity-50 font-medium transition-colors"
      >
        {isSubmitting ? 'Creating request...' : 'Create Delink Request'}
      </button>
    </form>
  );
};
