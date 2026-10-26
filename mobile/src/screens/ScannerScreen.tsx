import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Colors } from '../theme/colors';
import { Ionicons } from '@expo/vector-icons';
import { ApiService } from '../services/api';
import { RetryGuardModal } from '../components/RetryGuardModal';

const { width } = Dimensions.get('window');
const SCAN_FRAME_SIZE = width * 0.72;

interface ScannerScreenProps {
  navigation: any;
}

export const ScannerScreen: React.FC<ScannerScreenProps> = ({ navigation }) => {
  const [permission, requestPermission] = useCameraPermissions();
  const [torch, setTorch] = useState(false);
  const [scanning, setScanning] = useState(true);
  const [loading, setLoading] = useState(false);

  // Pre-flight verified merchant modal state
  const [verifiedMerchant, setVerifiedMerchant] = useState<any>(null);
  const [duplicateWarning, setDuplicateWarning] = useState<any>(null);
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [pendingScanCode, setPendingScanCode] = useState<string | null>(null);

  const demoMerchants = [
    { id: 'merch_grocery_01', name: 'Demo Grocery Store (₹4,000)', code: 'grocery@paytm', amount: 4000.0 },
    { id: 'merch_cafe_02', name: 'Demo Cafe (₹750)', code: 'cafe@paytm', amount: 750.0 },
    { id: 'merch_pharmacy_03', name: 'Demo Pharmacy (₹1,200)', code: 'pharmacy@paytm', amount: 1200.0 },
  ];

  const handleBarcodeScanned = async ({ data }: { data: string }) => {
    if (!scanning || loading) return;
    setScanning(false);
    processQRCode(data);
  };

  const processQRCode = async (code: string, bypassDuplicate: boolean = false) => {
    try {
      setLoading(true);
      setPendingScanCode(code);
      const res = await ApiService.resolveQR(code);

      if (!res.valid) {
        Alert.alert('Unsupported QR', res.error_message || 'Please scan a valid demo merchant QR code.', [
          { text: 'Try Again', onPress: () => setScanning(true) },
        ]);
        return;
      }

      setVerifiedMerchant(res.merchant);

      // Check RetryGuard duplicate alert
      if (res.duplicate_check?.has_potential_duplicate && !bypassDuplicate) {
        setDuplicateWarning(res.duplicate_check);
        setShowDuplicateModal(true);
      } else {
        // Ready to proceed to payment confirmation
      }
    } catch (err: any) {
      Alert.alert('Scan Resolution Error', err.message || 'Failed to verify merchant details.', [
        { text: 'Retry', onPress: () => setScanning(true) },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const executePayment = async (scenario: string = 'OUTCOME_UNKNOWN', acknowledged: boolean = false) => {
    if (!verifiedMerchant) return;

    try {
      setLoading(true);
      const order = await ApiService.createTestOrder({
        merchant_id: verifiedMerchant.id,
        amount: verifiedMerchant.default_amount,
        force_scenario: scenario,
        acknowledged_duplicate: acknowledged,
      });

      // Navigate to Payment Result screen
      navigation.replace('PaymentResult', {
        transactionId: order.transaction_id,
        amount: order.amount,
        merchantName: order.merchant_name,
        status: order.status,
      });
    } catch (err: any) {
      if (err.response?.status === 409) {
        // RetryGuard blocked backend execution
        setDuplicateWarning({
          warning_message: err.response.data?.detail?.message,
          existing_transaction_id: err.response.data?.detail?.existing_transaction_id,
        });
        setShowDuplicateModal(true);
      } else {
        Alert.alert('Payment Error', err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Native Camera View or Permission Handler */}
      {!permission?.granted ? (
        <View style={styles.permissionBox}>
          <Ionicons name="camera-outline" size={54} color={Colors.paytmLightBlue} />
          <Text style={styles.permissionTitle}>Camera Access Required</Text>
          <Text style={styles.permissionSubtitle}>
            To scan Paytm UPI QR codes with real-time RetryGuard protection, allow camera access.
          </Text>
          <TouchableOpacity style={styles.grantBtn} onPress={requestPermission} activeOpacity={0.8}>
            <Text style={styles.grantBtnText}>Grant Camera Permission</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <CameraView
          style={StyleSheet.absoluteFill}
          facing="back"
          enableTorch={torch}
          barcodeScannerSettings={{
            barcodeTypes: ['qr'],
          }}
          onBarcodeScanned={handleBarcodeScanned}
        />
      )}

      {/* Dark Overlay with Transparent QR Center */}
      <View style={styles.overlayContainer}>
        {/* Top Controls Bar */}
        <View style={styles.topControlRow}>
          <TouchableOpacity
            style={styles.circleBtn}
            onPress={() => navigation.goBack()}
            activeOpacity={0.7}
          >
            <Ionicons name="arrow-back" size={22} color={Colors.textWhite} />
          </TouchableOpacity>

          <Text style={styles.headerScanTitle}>Scan Any QR Code</Text>

          <TouchableOpacity
            style={[styles.circleBtn, torch && styles.torchActiveBtn]}
            onPress={() => setTorch(!torch)}
            activeOpacity={0.7}
          >
            <Ionicons name={torch ? 'flash' : 'flash-outline'} size={20} color={Colors.textWhite} />
          </TouchableOpacity>
        </View>

        {/* Scan Reticle Frame */}
        <View style={styles.reticleFrame}>
          <View style={[styles.corner, styles.cornerTL]} />
          <View style={[styles.corner, styles.cornerTR]} />
          <View style={[styles.corner, styles.cornerBL]} />
          <View style={[styles.corner, styles.cornerBR]} />

          {loading && (
            <View style={styles.reticleLoading}>
              <ActivityIndicator size="large" color={Colors.paytmLightBlue} />
              <Text style={styles.reticleLoadingText}>Verifying merchant & RetryGuard...</Text>
            </View>
          )}
        </View>

        <Text style={styles.scanInstruction}>
          Align QR code within the frame. RetryGuard will pre-check for unconfirmed duplicates.
        </Text>

        {/* Quick Demo QR Selector (for smooth presentation testing) */}
        <View style={styles.quickSelectorBox}>
          <Text style={styles.quickSelectorHeading}>DEMO QR QUICK-SELECT</Text>
          <View style={styles.demoQrButtonsRow}>
            {demoMerchants.map((dm) => (
              <TouchableOpacity
                key={dm.id}
                style={styles.demoQrChip}
                onPress={() => processQRCode(dm.code)}
                disabled={loading}
                activeOpacity={0.8}
              >
                <Text style={styles.demoQrChipText}>{dm.name.split(' (')[0]}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Verified Merchant Confirmation Drawer when scanned */}
        {verifiedMerchant && !showDuplicateModal && (
          <View style={styles.merchantDrawer}>
            <View style={styles.drawerHeader}>
              <View style={styles.verifiedTag}>
                <Ionicons name="checkmark-circle" size={14} color={Colors.successGreen} style={{ marginRight: 4 }} />
                <Text style={styles.verifiedTagText}>VERIFIED DEMO MERCHANT</Text>
              </View>
              <TouchableOpacity
                onPress={() => {
                  setVerifiedMerchant(null);
                  setScanning(true);
                }}
              >
                <Ionicons name="close" size={20} color={Colors.textSecondary} />
              </TouchableOpacity>
            </View>

            <View style={styles.drawerBody}>
              <View style={styles.merchantIconWrap}>
                <Text style={{ fontSize: 22 }}>{verifiedMerchant.logo_symbol || '🛒'}</Text>
              </View>
              <View style={{ flex: 1, marginLeft: 10 }}>
                <Text style={styles.drawerMerchantName}>{verifiedMerchant.name}</Text>
                <Text style={styles.drawerMerchantUpi}>{verifiedMerchant.upi_vpa}</Text>
              </View>
              <Text style={styles.drawerAmount}>₹{verifiedMerchant.default_amount.toLocaleString('en-IN')}</Text>
            </View>

            {/* Action Buttons to test different outcomes */}
            <View style={styles.checkoutActionRow}>
              <TouchableOpacity
                style={styles.payUnknownBtn}
                onPress={() => executePayment('OUTCOME_UNKNOWN', false)}
                disabled={loading}
                activeOpacity={0.85}
              >
                <Text style={styles.payBtnText}>Pay ₹{verifiedMerchant.default_amount} (Test Case)</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </View>

      {/* RetryGuard Warning Modal */}
      <RetryGuardModal
        visible={showDuplicateModal}
        onClose={() => {
          setShowDuplicateModal(false);
          setScanning(true);
        }}
        onViewPrevious={(txId) => {
          setShowDuplicateModal(false);
          navigation.navigate('PaymentRescue', { transactionId: txId });
        }}
        onContinueAnyway={() => {
          setShowDuplicateModal(false);
          executePayment('OUTCOME_UNKNOWN', true);
        }}
        warningMessage={duplicateWarning?.warning_message}
        existingTransactionId={duplicateWarning?.existing_transaction_id}
        existingAmount={duplicateWarning?.existing_amount}
        elapsedMinutes={duplicateWarning?.elapsed_minutes}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  permissionBox: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 30,
    backgroundColor: Colors.paytmDeepBlue,
  },
  permissionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.textWhite,
    marginTop: 14,
    marginBottom: 8,
  },
  permissionSubtitle: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.75)',
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 20,
  },
  grantBtn: {
    backgroundColor: Colors.paytmLightBlue,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 10,
  },
  grantBtnText: {
    color: Colors.paytmDeepBlue,
    fontSize: 14,
    fontWeight: '700',
  },
  overlayContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.45)',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 45,
    paddingBottom: 24,
  },
  topControlRow: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
  },
  circleBtn: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: 'rgba(0, 0, 0, 0.55)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  torchActiveBtn: {
    backgroundColor: Colors.warningOrange,
  },
  headerScanTitle: {
    color: Colors.textWhite,
    fontSize: 16,
    fontWeight: '700',
  },
  reticleFrame: {
    width: SCAN_FRAME_SIZE,
    height: SCAN_FRAME_SIZE,
    borderRadius: 16,
    backgroundColor: 'transparent',
    position: 'relative',
    justifyContent: 'center',
    alignItems: 'center',
  },
  corner: {
    position: 'absolute',
    width: 26,
    height: 26,
    borderColor: Colors.paytmLightBlue,
  },
  cornerTL: {
    top: 0,
    left: 0,
    borderTopWidth: 4,
    borderLeftWidth: 4,
    borderTopLeftRadius: 10,
  },
  cornerTR: {
    top: 0,
    right: 0,
    borderTopWidth: 4,
    borderRightWidth: 4,
    borderTopRightRadius: 10,
  },
  cornerBL: {
    bottom: 0,
    left: 0,
    borderBottomWidth: 4,
    borderLeftWidth: 4,
    borderBottomLeftRadius: 10,
  },
  cornerBR: {
    bottom: 0,
    right: 0,
    borderBottomWidth: 4,
    borderRightWidth: 4,
    borderBottomRightRadius: 10,
  },
  reticleLoading: {
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  reticleLoadingText: {
    color: Colors.textWhite,
    fontSize: 11,
    fontWeight: '600',
    marginTop: 8,
  },
  scanInstruction: {
    color: 'rgba(255, 255, 255, 0.85)',
    fontSize: 12,
    textAlign: 'center',
    paddingHorizontal: 30,
    marginTop: 10,
  },
  quickSelectorBox: {
    width: '90%',
    backgroundColor: 'rgba(0, 0, 0, 0.65)',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  quickSelectorHeading: {
    color: Colors.paytmLightBlue,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.8,
    marginBottom: 8,
    textAlign: 'center',
  },
  demoQrButtonsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 6,
  },
  demoQrChip: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    paddingVertical: 7,
    paddingHorizontal: 6,
    borderRadius: 6,
    alignItems: 'center',
  },
  demoQrChipText: {
    color: Colors.textWhite,
    fontSize: 10.5,
    fontWeight: '700',
  },
  merchantDrawer: {
    width: '92%',
    backgroundColor: Colors.cardBackground,
    borderRadius: 18,
    padding: 16,
    elevation: 6,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
  },
  drawerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  verifiedTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.successLight,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  verifiedTagText: {
    fontSize: 10,
    fontWeight: '800',
    color: Colors.successGreen,
    letterSpacing: 0.4,
  },
  drawerBody: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  merchantIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: Colors.surfaceLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  drawerMerchantName: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  drawerMerchantUpi: {
    fontSize: 11,
    color: Colors.textMuted,
    marginTop: 1,
  },
  drawerAmount: {
    fontSize: 18,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  checkoutActionRow: {
    flexDirection: 'row',
  },
  payUnknownBtn: {
    flex: 1,
    backgroundColor: Colors.paytmBlue,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
  },
  payBtnText: {
    color: Colors.textWhite,
    fontSize: 14,
    fontWeight: '700',
  },
});
