'use client';

import { useEffect, useState } from 'react';
import { securityService, MFARecoveryCode } from '@/services/security.service';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/components/ui/toast';
import { LoadingOverlay } from '@/components/ui/loading-overlay';
import { Dialog } from '@/components/ui/dialog';

export function MFARecovery() {
  const [codes, setCodes] = useState<MFARecoveryCode[]>([]);
  const [newCodes, setNewCodes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showNewCodesDialog, setShowNewCodesDialog] = useState(false);

  useEffect(() => {
    loadCodes();
  }, []);

  const loadCodes = async () => {
    try {
      setLoading(true);
      const data = await securityService.getRecoveryCodes();
      setCodes(data);
    } catch (error) {
      console.error(error);
      // No codes yet is expected
      setCodes([]);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateCodes = async () => {
    try {
      setGenerating(true);
      const response = await securityService.generateRecoveryCodes();
      setNewCodes(response.codes);
      setShowNewCodesDialog(true);
      toast.success('Recovery codes generated successfully');
    } catch (error) {
      toast.error('Failed to generate recovery codes');
      console.error(error);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadCodes = () => {
    const codesText = newCodes.join('\n');
    const blob = new Blob([codesText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'mfa-recovery-codes.txt';
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Recovery codes downloaded');
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    toast.success('Code copied to clipboard');
  };

  const handleCloseDialog = async () => {
    setShowNewCodesDialog(false);
    setNewCodes([]);
    await loadCodes();
  };

  if (loading) {
    return <LoadingOverlay />;
  }

  const unusedCodes = codes.filter(c => !c.used);
  const usedCodes = codes.filter(c => c.used);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">MFA Recovery Codes</h2>
        <p className="text-sm text-muted-foreground">
          Recovery codes let you access your account if you lose your MFA device
        </p>
      </div>

      {codes.length === 0 ? (
        <div className="border rounded-lg p-8 text-center">
          <p className="text-lg font-medium mb-2">🔑 No Recovery Codes</p>
          <p className="text-sm text-muted-foreground mb-4">
            Generate backup codes to regain access if you lose your MFA device
          </p>
          <Button onClick={handleGenerateCodes} disabled={generating}>
            {generating ? 'Generating...' : 'Generate Recovery Codes'}
          </Button>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium">
                  {unusedCodes.length} of {codes.length} codes remaining
                </p>
              </div>
              <Button onClick={handleGenerateCodes} disabled={generating}>
                {generating ? 'Generating...' : 'Generate New Codes'}
              </Button>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {codes.map((codeObj, index) => (
                <div
                  key={index}
                  className={`border rounded-lg p-3 flex justify-between items-center ${
                    codeObj.used ? 'bg-gray-50 dark:bg-gray-900 opacity-50' : ''
                  }`}
                >
                  <div>
                    <code className="text-sm font-mono">
                      {codeObj.used ? '••••••••' : codeObj.code}
                    </code>
                    {codeObj.used && (
                      <Badge variant="neutral" className="ml-2">Used</Badge>
                    )}
                  </div>
                  {!codeObj.used && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleCopyCode(codeObj.code)}
                    >
                      📋 Copy
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              ⚠️ <strong>Important:</strong> Each code can only be used once. Keep them in a safe place. Generating new codes will invalidate the old ones.
            </p>
          </div>
        </>
      )}

      {/* New Codes Dialog */}
      {showNewCodesDialog && (
        <Dialog
          isOpen={showNewCodesDialog}
          onClose={handleCloseDialog}
          title="🔐 Your New Recovery Codes"
          description="Save these codes in a safe place. Each code can only be used once."
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2">
              {newCodes.map((code, index) => (
                <div key={index} className="border rounded p-2 text-center">
                  <code className="text-sm font-mono font-bold">{code}</code>
                </div>
              ))}
            </div>

            <div className="flex gap-2">
              <Button onClick={handleDownloadCodes} className="flex-1">
                💾 Download as Text File
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  navigator.clipboard.writeText(newCodes.join('\n'));
                  toast.success('All codes copied!');
                }}
                className="flex-1"
              >
                📋 Copy All
              </Button>
            </div>

            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
              <p className="text-sm text-red-800 dark:text-red-200">
                ⚠️ <strong>Warning:</strong> These codes will only be shown once. Make sure to save them before closing this dialog.
              </p>
            </div>

            <Button onClick={handleCloseDialog} variant="outline" className="w-full">
              I've Saved My Codes
            </Button>
          </div>
        </Dialog>
      )}
    </div>
  );
}
