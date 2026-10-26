import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Ionicons } from '@expo/vector-icons';
import { PaytmHeader } from '../components/PaytmHeader';
import { FloatingAskRaah } from '../components/FloatingAskRaah';
import { AskRaahModal } from '../components/AskRaahModal';
import { ScenarioDrawer } from '../components/ScenarioDrawer';
import { ApiService } from '../services/api';

interface HomeScreenProps {
  navigation: any;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({ navigation }) => {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [healthData, setHealthData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [showAskRaah, setShowAskRaah] = useState(false);
  const [showDemoMenu, setShowDemoMenu] = useState(false);
  const [isOpsMode, setIsOpsMode] = useState(false);

  // Find any unresolved payment needing immediate attention
  const paymentNeedingAttention = transactions.find(
    (t) => t.status === 'OUTCOME_UNKNOWN' || t.status === 'DEBIT_REPORTED'
  );

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [txList, health] = await Promise.all([
        ApiService.listTransactions(15),
        ApiService.getSystemHealth(),
      ]);
      setTransactions(txList);
      setHealthData(health);
    } catch (err) {
      console.error('Failed to load home data', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const unsubscribe = navigation.addListener('focus', () => {
      loadData();
    });
    return unsubscribe;
  }, [navigation, loadData]);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const getStatusBadgeStyle = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return { bg: Colors.successLight, text: Colors.successGreen };
      case 'FAILED':
        return { bg: Colors.errorLight, text: Colors.errorRed };
      case 'REVERSED':
        return { bg: Colors.paytmCyan, text: Colors.paytmBlue };
      case 'OUTCOME_UNKNOWN':
      case 'DEBIT_REPORTED':
      default:
        return { bg: Colors.warningLight, text: Colors.warningOrange };
    }
  };

  return (
    <View style={styles.container}>
      <PaytmHeader
        onOpenDemoMenu={() => setShowDemoMenu(true)}
        isOpsMode={isOpsMode}
        onToggleRole={() => {
          if (!isOpsMode) {
            navigation.navigate('PulseOperations');
          } else {
            setIsOpsMode(false);
          }
        }}
      />

      <ScrollView
        style={styles.scrollArea}
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.paytmBlue]} />}
      >
        {/* Primary Scan & Pay Hero Card */}
        <View style={styles.heroCard}>
          <View style={styles.heroLeftCol}>
            <Text style={styles.heroTitle}>Scan with confidence.</Text>
            <Text style={styles.heroSubtitle}>Resolve with intelligence.</Text>
            <Text style={styles.heroDesc}>
              Built-in RetryGuard protects against accidental double debits.
            </Text>

            <TouchableOpacity
              style={styles.scanPayBtn}
              onPress={() => navigation.navigate('Scanner')}
              activeOpacity={0.85}
            >
              <Ionicons name="scan-outline" size={20} color={Colors.textWhite} style={{ marginRight: 8 }} />
              <Text style={styles.scanPayBtnText}>Scan Any QR Code</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.heroRightCol}>
            <View style={styles.qrIconWrap}>
              <Ionicons name="qr-code" size={54} color={Colors.paytmBlue} />
            </View>
          </View>
        </View>

        {/* PAYMENTS NEEDING ATTENTION (Highlighted if unresolved transaction exists) */}
        {paymentNeedingAttention && (
          <View style={styles.attentionCard}>
            <View style={styles.attentionHeader}>
              <View style={styles.attentionTag}>
                <Ionicons name="alert-circle" size={14} color={Colors.warningOrange} style={{ marginRight: 4 }} />
                <Text style={styles.attentionTagText}>PAYMENT NEEDING ATTENTION</Text>
              </View>
              <View style={styles.rescueActivePill}>
                <Text style={styles.rescueActiveText}>Rescue Active</Text>
              </View>
            </View>

            <View style={styles.attentionBody}>
              <View>
                <Text style={styles.attentionMerchant}>{paymentNeedingAttention.merchant_name}</Text>
                <Text style={styles.attentionReason}>
                  Account debited; merchant confirmation unverified.
                </Text>
              </View>
              <Text style={styles.attentionAmount}>₹{paymentNeedingAttention.amount.toLocaleString('en-IN')}</Text>
            </View>

            <TouchableOpacity
              style={styles.resolveNowBtn}
              onPress={() =>
                navigation.navigate('PaymentRescue', { transactionId: paymentNeedingAttention.id })
              }
              activeOpacity={0.85}
            >
              <Ionicons name="shield-checkmark" size={16} color={Colors.textWhite} style={{ marginRight: 6 }} />
              <Text style={styles.resolveNowBtnText}>Track & Resolve Payment</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Raah Pulse Operational Status Pill */}
        <TouchableOpacity
          style={styles.pulseCard}
          onPress={() => navigation.navigate('PulseOperations')}
          activeOpacity={0.85}
        >
          <View style={styles.pulseIconCircle}>
            <Ionicons name="pulse" size={20} color={Colors.accentPurple} />
          </View>
          <View style={styles.pulseTextCol}>
            <View style={styles.pulseHeaderRow}>
              <Text style={styles.pulseTitle}>Raah Pulse Teammate</Text>
              <View style={[styles.pulseStatusBadge, healthData?.system_status === 'HEALTHY' ? styles.pulseHealthy : styles.pulseActive]}>
                <Text style={styles.pulseStatusText}>
                  {healthData?.system_status === 'HEALTHY' ? 'SYSTEM NORMAL' : 'ANOMALY DETECTED'}
                </Text>
              </View>
            </View>
            <Text style={styles.pulseDesc}>
              {healthData?.active_incidents_count
                ? `${healthData.active_incidents_count} shared incident active. 12 transactions correlated.`
                : 'Payment health telemetry: All gateway routes normal.'}
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color={Colors.textMuted} />
        </TouchableOpacity>

        {/* Quick Demo Scenarios Row */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>QUICK SCENARIO DEMOS</Text>
          <TouchableOpacity onPress={() => setShowDemoMenu(true)}>
            <Text style={styles.seeAllText}>View All 8</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.quickChipsContainer}>
          <TouchableOpacity
            style={styles.quickScenarioBtn}
            onPress={async () => {
              await ApiService.triggerScenario('3', 4000.0);
              loadData();
              navigation.navigate('PaymentRescue', { transactionId: 'tx_demo_4000_grocery' });
            }}
            activeOpacity={0.8}
          >
            <Ionicons name="alert-circle-outline" size={16} color={Colors.warningOrange} style={{ marginRight: 6 }} />
            <Text style={styles.quickScenarioText}>₹4,000 Debit/Unknown</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.quickScenarioBtn}
            onPress={async () => {
              await ApiService.triggerScenario('5', 4000.0);
              loadData();
              navigation.navigate('PaymentRescue', { transactionId: 'tx_demo_4000_grocery' });
            }}
            activeOpacity={0.8}
          >
            <Ionicons name="checkmark-done-circle-outline" size={16} color={Colors.successGreen} style={{ marginRight: 6 }} />
            <Text style={styles.quickScenarioText}>Simulate Reversal</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.quickScenarioBtn}
            onPress={async () => {
              await ApiService.triggerScenario('6', 4000.0);
              loadData();
              navigation.navigate('PulseOperations');
            }}
            activeOpacity={0.8}
          >
            <Ionicons name="git-network-outline" size={16} color={Colors.accentPurple} style={{ marginRight: 6 }} />
            <Text style={styles.quickScenarioText}>12-Tx Pulse Spike</Text>
          </TouchableOpacity>
        </View>

        {/* Recent Transactions Section */}
        <View style={[styles.sectionHeaderRow, { marginTop: 18 }]}>
          <Text style={styles.sectionTitle}>RECENT TRANSACTIONS</Text>
          <Text style={styles.txCountText}>{transactions.length} items</Text>
        </View>

        {loading && transactions.length === 0 ? (
          <ActivityIndicator size="small" color={Colors.paytmBlue} style={{ marginVertical: 20 }} />
        ) : (
          <View style={styles.txListCard}>
            {transactions.slice(0, 8).map((tx, idx) => {
              const badgeStyle = getStatusBadgeStyle(tx.status);
              const isLast = idx === Math.min(transactions.length, 8) - 1;

              return (
                <TouchableOpacity
                  key={tx.id || idx}
                  style={[styles.txItemRow, isLast && styles.lastTxItem]}
                  onPress={() => {
                    navigation.navigate('PaymentRescue', { transactionId: tx.id });
                  }}
                  activeOpacity={0.7}
                >
                  <View style={styles.txIconBox}>
                    <Text style={styles.txIconSymbol}>
                      {tx.merchant_name.includes('Cafe') ? '☕' : tx.merchant_name.includes('Pharmacy') ? '💊' : '🛒'}
                    </Text>
                  </View>

                  <View style={styles.txDetailsCol}>
                    <Text style={styles.txMerchantName} numberOfLines={1}>{tx.merchant_name}</Text>
                    <Text style={styles.txBankDetails}>{tx.payer_bank} • {tx.id}</Text>
                  </View>

                  <View style={styles.txAmountCol}>
                    <Text style={styles.txAmountText}>₹{tx.amount.toLocaleString('en-IN')}</Text>
                    <View style={[styles.txStatusBadge, { backgroundColor: badgeStyle.bg }]}>
                      <Text style={[styles.txStatusBadgeText, { color: badgeStyle.text }]}>
                        {tx.status === 'OUTCOME_UNKNOWN' ? 'UNCERTAIN' : tx.status}
                      </Text>
                    </View>
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        )}
      </ScrollView>

      {/* Floating Ask Raah Button */}
      <FloatingAskRaah
        onPress={() => setShowAskRaah(true)}
        hasUnread={!!paymentNeedingAttention}
      />

      {/* Contextual Ask Raah Bottom Sheet */}
      <AskRaahModal
        visible={showAskRaah}
        onClose={() => setShowAskRaah(false)}
        transactionId={paymentNeedingAttention?.id || transactions[0]?.id}
        transactionAmount={paymentNeedingAttention?.amount || transactions[0]?.amount}
        merchantName={paymentNeedingAttention?.merchant_name || transactions[0]?.merchant_name}
      />

      {/* Demo Scenario Control Center */}
      <ScenarioDrawer
        visible={showDemoMenu}
        onClose={() => setShowDemoMenu(false)}
        onScenarioTriggered={(id) => {
          loadData();
          if (id === '6') {
            navigation.navigate('PulseOperations');
          } else {
            navigation.navigate('PaymentRescue', { transactionId: 'tx_demo_4000_grocery' });
          }
        }}
        onResetComplete={loadData}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollArea: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 90,
  },
  heroCard: {
    backgroundColor: Colors.cardBackground,
    borderRadius: 18,
    marginHorizontal: 16,
    marginTop: 14,
    padding: 18,
    flexDirection: 'row',
    alignItems: 'center',
    elevation: 3,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  heroLeftCol: {
    flex: 1,
  },
  heroTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: Colors.paytmDeepBlue,
  },
  heroSubtitle: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.paytmLightBlue,
    marginTop: 1,
  },
  heroDesc: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginTop: 4,
    lineHeight: 15,
  },
  scanPayBtn: {
    backgroundColor: Colors.paytmBlue,
    borderRadius: 10,
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 14,
    marginTop: 12,
    alignSelf: 'flex-start',
  },
  scanPayBtnText: {
    color: Colors.textWhite,
    fontSize: 13,
    fontWeight: '700',
  },
  heroRightCol: {
    marginLeft: 12,
  },
  qrIconWrap: {
    width: 78,
    height: 78,
    borderRadius: 16,
    backgroundColor: Colors.paytmCyan,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: 'rgba(0, 186, 242, 0.3)',
  },
  attentionCard: {
    backgroundColor: '#FFFBEB',
    borderRadius: 16,
    marginHorizontal: 16,
    marginTop: 14,
    padding: 16,
    borderWidth: 1.5,
    borderColor: Colors.warningOrange,
  },
  attentionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  attentionTag: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  attentionTagText: {
    fontSize: 10.5,
    fontWeight: '800',
    color: Colors.warningOrange,
    letterSpacing: 0.5,
  },
  rescueActivePill: {
    backgroundColor: Colors.warningOrange,
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 10,
  },
  rescueActiveText: {
    fontSize: 9.5,
    fontWeight: '800',
    color: Colors.textWhite,
  },
  attentionBody: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  attentionMerchant: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  attentionReason: {
    fontSize: 11.5,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  attentionAmount: {
    fontSize: 20,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  resolveNowBtn: {
    backgroundColor: Colors.paytmBlue,
    borderRadius: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
  },
  resolveNowBtnText: {
    color: Colors.textWhite,
    fontSize: 13,
    fontWeight: '700',
  },
  pulseCard: {
    backgroundColor: Colors.cardBackground,
    borderRadius: 16,
    marginHorizontal: 16,
    marginTop: 12,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(124, 58, 237, 0.2)',
  },
  pulseIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(124, 58, 237, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  pulseTextCol: {
    flex: 1,
  },
  pulseHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 2,
  },
  pulseTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  pulseStatusBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  pulseHealthy: {
    backgroundColor: Colors.successLight,
  },
  pulseActive: {
    backgroundColor: 'rgba(124, 58, 237, 0.15)',
  },
  pulseStatusText: {
    fontSize: 9,
    fontWeight: '800',
    color: Colors.accentPurple,
  },
  pulseDesc: {
    fontSize: 11,
    color: Colors.textSecondary,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 18,
    marginTop: 16,
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '800',
    color: Colors.textMuted,
    letterSpacing: 0.8,
  },
  seeAllText: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.paytmLightBlue,
  },
  txCountText: {
    fontSize: 10.5,
    color: Colors.textMuted,
  },
  quickChipsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 8,
  },
  quickScenarioBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.cardBackground,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  quickScenarioText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
  txListCard: {
    backgroundColor: Colors.cardBackground,
    borderRadius: 16,
    marginHorizontal: 16,
    borderWidth: 1,
    borderColor: Colors.border,
    paddingHorizontal: 14,
  },
  txItemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
  },
  lastTxItem: {
    borderBottomWidth: 0,
  },
  txIconBox: {
    width: 38,
    height: 38,
    borderRadius: 10,
    backgroundColor: Colors.surfaceLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  txIconSymbol: {
    fontSize: 18,
  },
  txDetailsCol: {
    flex: 1,
  },
  txMerchantName: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  txBankDetails: {
    fontSize: 11,
    color: Colors.textMuted,
    marginTop: 2,
  },
  txAmountCol: {
    alignItems: 'flex-end',
  },
  txAmountText: {
    fontSize: 14,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  txStatusBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginTop: 3,
  },
  txStatusBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
});
