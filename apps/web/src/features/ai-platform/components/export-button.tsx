import * as React from 'react';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';
import { toast } from '@/components/ui/toast';

interface ExportButtonProps {
  data: any[];
  filename?: string;
  label?: string;
}

export function ExportButton({ data, filename = 'export.csv', label = 'Export CSV' }: ExportButtonProps) {
  const handleExport = () => {
    if (!data || !data.length) {
      toast.error('No Data', 'There is no data to export.');
      return;
    }

    try {
      const headers = Object.keys(data[0]);
      const csvRows = [
        headers.join(','), // Header row
        ...data.map((row) =>
          headers
            .map((fieldName) => {
              const value = row[fieldName];
              const stringValue = value === null || value === undefined ? '' : String(value);
              // Escape quotes
              return `"${stringValue.replace(/"/g, '""')}"`;
            })
            .join(',')
        ),
      ];

      // Use a Blob and URL.createObjectURL for robust file downloads (works with larger files too)
      const csvBlob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(csvBlob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      toast.success('Export Successful', `Data downloaded as ${filename}.`);
    } catch (e) {
      toast.error('Export Failed', 'An error occurred during file generation.');
      console.error(e);
    }
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleExport}
      className="gap-1.5 h-8 text-[11px] bg-neutral-900 border-white/5 hover:bg-neutral-950 font-medium"
    >
      <Download className="w-3.5 h-3.5" />
      {label}
    </Button>
  );
}
