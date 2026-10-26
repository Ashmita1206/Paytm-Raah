import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Ionicons } from '@expo/vector-icons';
import { ApiService } from '../services/api';

interface PaymentResultScreenProps {
  route: any;
  navigation: any;
}

export const PaymentResultScreen: React.FC<PaymentResultScreenProps> = ({
  route,
  navigation,
}) => {
  const { transactionId, amount, merchantName, status: initialStatus } = route.params || {};
  const [transaction, setTransaction] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTransaction();
  }, [transactionId]);

  const loadTransaction = async () => {
    try {
      if (transactionId) {
        const tx = await ApiService.getTransaction(transactionId);
        setTransaction(tx);
      }
    } catch (e) {
      console.error('Failed to load transaction result', e);
    } finally {
      setLoading(false);
    }
  };

  const status = transaction?.status || initialStatus || 'OUTCOME_UNKNOWN';
  const isSuccess = status === 'SUCCESS';
  const isFailed = status === 'FAILED';
  const isUnknown = status === 'OUTCOME_UNKNOWN' || status === 'DEBIT_REPORTED';

  const getStatusConfig = () => {
    if (isSuccess) {
      return {
        icon: 'checkmark-circle',
        color: Colors.successGreen,
        bg: Colors.successLight,
        title: 'Payment Successful',
        subtitle: `₹${(amount || transaction?.amount || 0).toLocaleString('en-IN')} paid to ${merchantName || transaction?.merchant_name}`,
        desc: 'Verified by payment switch and confirmed settled by merchant.',
      };
    }
    if (isFailed) {
      return {
        icon: 'close-circle',
        color: Colors.errorRed,
        bg: Colors.errorLight,
        title: 'Payment Rejected',
        subtitle: `₹${(amount || transaction?.amount || 0).toLocaleString('en-IN')} failed before debit`,
        desc: transaction?.failure_reason || 'Authentication failed. No money transferred from your bank account.',
      };
    }
    return {
      icon: 'help-circle',
      color: Colors.warningOrange,
      bg: Colors.warningLight,
      title: 'Payment Status Uncertain',
      subtitle: `₹${(amount || transaction?.amount || 0).toLocaleString('en-IN')} debited, merchant confirmation pending`,
      desc: 'Raah Rescue has registered this payment and started autonomous verification across network switches.',
    };
  };

  const config = getStatusConfig();

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Top outcome banner */}
      <View style={[styles.heroCard, { backgroundColor: config.bg }]}>
        <Ionicons name={config.icon as any} size={64} color={config.color} style={{ marginBottom: 12 }} />
        <Text style={[styles.heroTitle, { color: config.color }]}>{config.title}</Text>
        <Text style={styles.heroAmount}>₹{(amount || transaction?.amount || 4000).toLocaleString('en-IN')}</Text>
        <Text style={styles.heroSubtitle}>{config.subtitle}</Text>
        <Text style={styles.heroDesc}>{config.desc}</Text>

        {isUnknown && (
          <View style={styles.rescueBadge}>
            <Ionicons name="shield-checkmark" size={14} color={Colors.paytmBlue} style={{ marginRight: 4 }} />
            <Text style={styles.rescueBadgeText}>Raah Rescue Investigation Active</Text>
          </View>
        )}
      </View>

      {/* Transaction Summary Card */}
      <View style={styles.detailsCard}>
        <Text style={styles.detailsHeader}>TRANSACTION DETAILS</Text>

        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Merchant</Text>
          <Text style={styles.detailValue}>{merchantName || transaction?.merchant_name || 'Demo Grocery Store'}</Text>
        </View>

        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Reference ID</Text>
          <Text style={styles.detailValueMono}>{transaction?.upi_ref_no || transactionId || 'UPI-2026-98741029'}</Text>
        </View>

        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Payer Bank</Text>
          <Text style={styles.detailValue}>{transaction?.payer_bank || 'HDFC Bank'}</Text>
        </View>

        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Payment Provider</Text>
          <Text style={styles.detailValue}>NPCI UPI Switch</Text>
        </View>

        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Verification Mode</Text>
          <Text style={styles.detailValue}>DEMO / SIMULATED</Text>
        </View>
      </View>

      {/* Primary Action Button */}
      {isUnknown ? (
        <TouchableOpacity
          style={styles.primaryActionButton}
          onPress={() => navigation.navigate('PaymentRescue', { transactionId: transactionId || transaction?.id })}
          activeOpacity={0.85}
        >
          <Ionicons name="shield-checkmark" size={18} color={Colors.textWhite} style={{ marginRight: 8 }} />
          <Text style={styles.primaryActionBtnText}>Track & Resolve Payment</Text>
        </TouchableOpacity>
      ) : (
        <TouchableOpacity
          style={styles.secondaryDoneBtn}
          onPress={() => navigation.navigate('Home')}
          activeOpacity={0.85}
        >
          <Text style={styles.secondaryDoneBtnText}>Back to Home</Text>
        </TouchableOpacity>
      )}

      {isUnknown && (
        <TouchableOpacity
          style={styles.homeLinkBtn}
          onPress={() => navigation.navigate('Home')}
          activeOpacity={0.7}
        >
          <Text style={styles.homeLinkBtnText}>Return to Home (Background Monitoring Active)</Text>
        </TouchableOpacity>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    padding: 20,
    paddingTop: 50,
  },
  heroCard: {
    borderRadius: 22,
    padding: 24,
    alignItems: 'center',
    marginBottom: 20,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  heroTitle: {
    fontSize: 20,
    fontWeight: '800',
    marginBottom: 6,
  },
  heroAmount: {
    fontSize: 34,
    fontWeight: '900',
    color: Colors.textPrimary,
    marginBottom: 4,
  },
  heroSubtitle: {
    fontSize: 13,
    color: Colors.textSecondary,
    textAlign: 'center',
    fontWeight: '600',
    marginBottom: 8,
  },
  heroDesc: {
    fontSize: 11.5,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 16,
    paddingHorizontal: 10,
  },
  rescueBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.paytmCyan,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
    marginTop: 14,
    borderWidth: 1,
    borderColor: 'rgba(0, 186, 242, 0.3)',
  },
  rescueBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.paytmBlue,
  },
  detailsCard: {
    backgroundColor: Colors.cardBackground,
    borderRadius: 16,
    padding: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  detailsHeader: {
    fontSize: 11,
    fontWeight: '800',
    color: Colors.textMuted,
    letterSpacing: 0.8,
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  detailLabel: {
    fontSize: 12.5,
    color: Colors.textSecondary,
  },
  detailValue: {
    fontSize: 12.5,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  detailValueMono: {
    fontSize: 11.5,
    fontWeight: '700',
    color: Colors.paytmBlue,
    fontFamily: 'monospace',
  },
  primaryActionButton: {
    backgroundColor: Colors.paytmBlue,
    borderRadius: 14,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
    elevation: 3,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  primaryActionBtnText: {
    color: Colors.textWhite,
    fontSize: 15,
    fontWeight: '800',
  },
  secondaryDoneBtn: {
    backgroundColor: Colors.paytmBlue,
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  secondaryDoneBtnText: {
    color: Colors.textWhite,
    fontSize: 15,
    fontWeight: '700',
  },
  homeLinkBtn: {
    paddingVertical: 10,
    alignItems: 'center',
  },
  homeLinkBtnText: {
    color: Colors.paytmLightBlue,
    fontSize: 12,
    fontWeight: '600',
  },
});
