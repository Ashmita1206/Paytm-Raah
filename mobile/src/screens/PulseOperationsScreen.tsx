import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Ionicons } from '@expo/vector-icons';
import { ApiService } from '../services/api';

interface PulseOperationsScreenProps {
  navigation: any;
}

export const PulseOperationsScreen: React.FC<PulseOperationsScreenProps> = ({
  navigation,
}) => {
  const [health, setHealth] = useState<any>(null);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<any>(null);
  const [linkedCases, setLinkedCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [acting, setActing] = useState(false);

  const loadPulseData = useCallback(async () => {
    try {
      const [hData, incList] = await Promise.all([
        ApiService.getSystemHealth(),
        ApiService.listIncidents(),
      ]);
      setHealth(hData);
      setIncidents(incList);

      if (incList && incList.length > 0) {
        const topInc = incList[0];
        setSelectedIncident(topInc);
        const detailed = await ApiService.getIncident(topInc.id);
        setLinkedCases(detailed.linked_cases || []);
      }
    } catch (e: any) {
      console.error('Failed to load Pulse operations data', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadPulseData();
  }, [loadPulseData]);

  const onRefresh = () => {
    setRefreshing(true);
    loadPulseData();
  };

  const handleReviewAction = async (action: string) => {
    if (!selectedIncident) return;
    try {
      setActing(true);
      await ApiService.reviewIncident(selectedIncident.id, action);
      await loadPulseData();
      Alert.alert('Action Executed', `Operational teammate executed: ${action}`);
    } catch (e: any) {
      Alert.alert('Review Action Failed', e.message);
    } finally {
      setActing(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Operations Navbar */}
      <View style={styles.navBar}>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()} activeOpacity={0.7}>
          <Ionicons name="arrow-back" size={22} color={Colors.textWhite} />
        </TouchableOpacity>
        <View style={styles.navTitleCol}>
          <View style={styles.navHeaderRow}>
            <Text style={styles.navTitle}>Raah Pulse Operations</Text>
            <View style={styles.opsBadge}>
              <Text style={styles.opsBadgeText}>SUPPORT OPS</Text>
            </View>
          </View>
          <Text style={styles.navSubtitle}>Autonomous Incident Detection & Coordination</Text>
        </View>
        <TouchableOpacity style={styles.refreshBtn} onPress={onRefresh} activeOpacity={0.7}>
          <Ionicons name="reload" size={18} color={Colors.textWhite} />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollArea}
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.accentPurple]} />}
      >
        {/* Payment Health Telemetry Card */}
        <View style={styles.healthCard}>
          <View style={styles.healthTopRow}>
            <View>
              <Text style={styles.healthLabel}>PAYMENT HEALTH TELEMETRY</Text>
              <Text style={styles.healthStatusText}>
                {health?.system_status === 'HEALTHY' ? '🟢 Normal Routing Active' : '🟡 Switch Anomaly Under Investigation'}
              </Text>
            </View>
            <View style={styles.successRateBox}>
              <Text style={styles.rateValue}>{health?.overall_success_rate || 96.4}%</Text>
              <Text style={styles.rateLabel}>Success Rate</Text>
            </View>
          </View>

          {/* Monitored Banks Grid */}
          <View style={styles.banksGrid}>
            {(health?.monitored_banks || []).map((b: any, i: number) => {
              const isDegraded = b.status === 'DEGRADED';
              return (
                <View key={i} style={[styles.bankItem, isDegraded ? styles.bankDegraded : styles.bankHealthy]}>
                  <View style={[styles.bankStatusDot, { backgroundColor: isDegraded ? Colors.errorRed : Colors.successGreen }]} />
                  <Text style={styles.bankName}>{b.bank.replace(' Bank', '')}</Text>
                  <Text style={styles.bankLatency}>{b.observed_latency_ms}ms</Text>
                </View>
              );
            })}
          </View>
        </View>

        {/* Selected Incident Detail */}
        {selectedIncident ? (
          <View style={styles.incidentCard}>
            <View style={styles.incidentHeader}>
              <View style={styles.incNumBadge}>
                <Ionicons name="flash" size={12} color={Colors.accentPurple} style={{ marginRight: 4 }} />
                <Text style={styles.incNumText}>{selectedIncident.incident_number}</Text>
              </View>
              <View style={[styles.statusTag, selectedIncident.status === 'RESOLVED' ? styles.statusGreen : styles.statusPurple]}>
                <Text style={styles.statusTagText}>{selectedIncident.status}</Text>
              </View>
            </View>

            <Text style={styles.incidentTitle}>{selectedIncident.title}</Text>
            <Text style={styles.incidentSummary}>{selectedIncident.summary}</Text>

            {/* Metrics Row: Observed vs Baseline */}
            <View style={styles.metricsRow}>
              <View style={styles.metricBox}>
                <Text style={styles.metricLabel}>Affected Volume</Text>
                <Text style={styles.metricValue}>{selectedIncident.affected_count} Transactions</Text>
              </View>
              <View style={styles.metricBox}>
                <Text style={styles.metricLabel}>Observed Rate</Text>
                <Text style={[styles.metricValue, { color: Colors.errorRed }]}>{selectedIncident.observed_failure_rate}%</Text>
              </View>
              <View style={styles.metricBox}>
                <Text style={styles.metricLabel}>Baseline TAT</Text>
                <Text style={styles.metricValue}>{selectedIncident.baseline_failure_rate}%</Text>
              </View>
            </View>

            {/* Recommended AI Mitigation */}
            <View style={styles.mitigationBox}>
              <View style={styles.mitigationHeader}>
                <Ionicons name="bulb-outline" size={15} color={Colors.accentPurple} style={{ marginRight: 6 }} />
                <Text style={styles.mitigationTitle}>AUTONOMOUS MITIGATION RECOMMENDATION</Text>
              </View>
              <Text style={styles.mitigationText}>{selectedIncident.recommended_mitigation}</Text>
            </View>

            {/* Operational Decision Controls */}
            <View style={styles.opsActionRow}>
              <TouchableOpacity
                style={styles.actionBtnMitigate}
                onPress={() => handleReviewAction('MITIGATE')}
                disabled={acting}
                activeOpacity={0.8}
              >
                <Text style={styles.actionBtnText}>Apply Dynamic Routing</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.actionBtnAdvisory}
                onPress={() => handleReviewAction('BROADCAST_ADVISORY')}
                disabled={acting}
                activeOpacity={0.8}
              >
                <Text style={styles.actionBtnTextDark}>Broadcast Advisory</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.actionBtnResolve}
                onPress={() => handleReviewAction('RESOLVE')}
                disabled={acting}
                activeOpacity={0.8}
              >
                <Text style={styles.actionBtnText}>Mark Resolved</Text>
              </TouchableOpacity>
            </View>

            {/* Linked Customer Recovery Cases */}
            <View style={styles.linkedSection}>
              <View style={styles.linkedHeader}>
                <Ionicons name="people-outline" size={16} color={Colors.paytmBlue} style={{ marginRight: 6 }} />
                <Text style={styles.linkedTitle}>Correlated Customer Cases ({linkedCases.length})</Text>
              </View>
              <Text style={styles.linkedSubtitle}>
                Raah Pulse automatically grouped these individual recovery cases to prevent fragmented support tickets.
              </Text>

              {linkedCases.slice(0, 6).map((lc, idx) => (
                <View key={lc.id || idx} style={styles.linkedCaseItem}>
                  <View style={styles.linkedCaseDot} />
                  <View style={styles.linkedCaseCol}>
                    <Text style={styles.linkedCaseTx}>Tx: {lc.transaction_id}</Text>
                    <Text style={styles.linkedCaseDetails}>
                      {lc.merchant_name || 'Demo Merchant'} • ₹{lc.transaction_amount?.toLocaleString('en-IN') || '4,000'}
                    </Text>
                  </View>
                  <View style={styles.confidenceBadge}>
                    <Text style={styles.confidenceText}>{(lc.correlation_confidence * 100).toFixed(0)}% Confidence</Text>
                  </View>
                </View>
              ))}
            </View>
          </View>
        ) : (
          <View style={styles.emptyIncBox}>
            <Text style={styles.emptyIncText}>No active failure clusters detected by Raah Pulse.</Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  navBar: {
    backgroundColor: Colors.accentPurple,
    paddingTop: 45,
    paddingBottom: 14,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    elevation: 4,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  navTitleCol: {
    flex: 1,
    marginHorizontal: 12,
  },
  navHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  navTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: Colors.textWhite,
  },
  opsBadge: {
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 4,
    marginLeft: 6,
  },
  opsBadgeText: {
    fontSize: 9,
    fontWeight: '800',
    color: Colors.textWhite,
  },
  navSubtitle: {
    fontSize: 10.5,
    color: 'rgba(255, 255, 255, 0.85)',
  },
  refreshBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollArea: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  healthCard: {
    backgroundColor: Colors.cardBackground,
    borderRadius: 18,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  healthTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  healthLabel: {
    fontSize: 10,
    fontWeight: '800',
    color: Colors.textMuted,
    letterSpacing: 0.6,
  },
  healthStatusText: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginTop: 2,
  },
  successRateBox: {
    alignItems: 'flex-end',
  },
  rateValue: {
    fontSize: 22,
    fontWeight: '800',
    color: Colors.successGreen,
  },
  rateLabel: {
    fontSize: 10,
    color: Colors.textSecondary,
  },
  banksGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  bankItem: {
    flex: 1,
    minWidth: '45%',
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 8,
    borderWidth: 1,
  },
  bankHealthy: {
    backgroundColor: Colors.surfaceLight,
    borderColor: Colors.border,
  },
  bankDegraded: {
    backgroundColor: Colors.errorLight,
    borderColor: 'rgba(229, 57, 53, 0.3)',
  },
  bankStatusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  bankName: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textPrimary,
    flex: 1,
  },
  bankLatency: {
    fontSize: 11,
    color: Colors.textMuted,
    fontWeight: '500',
  },
  incidentCard: {
    backgroundColor: Colors.cardBackground,
    borderRadius: 18,
    padding: 18,
    borderWidth: 1,
    borderColor: 'rgba(124, 58, 237, 0.25)',
  },
  incidentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  incNumBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(124, 58, 237, 0.12)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  incNumText: {
    fontSize: 11,
    fontWeight: '800',
    color: Colors.accentPurple,
  },
  statusTag: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  statusPurple: {
    backgroundColor: 'rgba(124, 58, 237, 0.15)',
  },
  statusGreen: {
    backgroundColor: Colors.successLight,
  },
  statusTagText: {
    fontSize: 10,
    fontWeight: '800',
    color: Colors.accentPurple,
  },
  incidentTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: Colors.textPrimary,
    marginBottom: 6,
  },
  incidentSummary: {
    fontSize: 12,
    color: Colors.textSecondary,
    lineHeight: 17,
    marginBottom: 14,
  },
  metricsRow: {
    flexDirection: 'row',
    backgroundColor: Colors.surfaceLight,
    borderRadius: 10,
    padding: 10,
    marginBottom: 14,
  },
  metricBox: {
    flex: 1,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 9.5,
    color: Colors.textMuted,
    fontWeight: '600',
  },
  metricValue: {
    fontSize: 13,
    fontWeight: '800',
    color: Colors.textPrimary,
    marginTop: 2,
  },
  mitigationBox: {
    backgroundColor: 'rgba(124, 58, 237, 0.07)',
    borderRadius: 10,
    padding: 12,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: 'rgba(124, 58, 237, 0.2)',
  },
  mitigationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  mitigationTitle: {
    fontSize: 10,
    fontWeight: '800',
    color: Colors.accentPurple,
    letterSpacing: 0.5,
  },
  mitigationText: {
    fontSize: 11.5,
    color: Colors.textPrimary,
    lineHeight: 16,
  },
  opsActionRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 18,
  },
  actionBtnMitigate: {
    flex: 1,
    backgroundColor: Colors.accentPurple,
    paddingVertical: 9,
    borderRadius: 8,
    alignItems: 'center',
  },
  actionBtnAdvisory: {
    flex: 1,
    backgroundColor: Colors.surfaceLight,
    paddingVertical: 9,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  actionBtnResolve: {
    flex: 1,
    backgroundColor: Colors.paytmBlue,
    paddingVertical: 9,
    borderRadius: 8,
    alignItems: 'center',
  },
  actionBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textWhite,
  },
  actionBtnTextDark: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  linkedSection: {
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
    paddingTop: 14,
  },
  linkedHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  linkedTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: Colors.paytmDeepBlue,
  },
  linkedSubtitle: {
    fontSize: 10.5,
    color: Colors.textMuted,
    marginBottom: 10,
  },
  linkedCaseItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceLight,
    padding: 10,
    borderRadius: 8,
    marginBottom: 6,
  },
  linkedCaseDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.paytmLightBlue,
    marginRight: 8,
  },
  linkedCaseCol: {
    flex: 1,
  },
  linkedCaseTx: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textPrimary,
    fontFamily: 'monospace',
  },
  linkedCaseDetails: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginTop: 1,
  },
  confidenceBadge: {
    backgroundColor: Colors.paytmCyan,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  confidenceText: {
    fontSize: 9,
    fontWeight: '700',
    color: Colors.paytmBlue,
  },
  emptyIncBox: {
    padding: 30,
    alignItems: 'center',
  },
  emptyIncText: {
    fontSize: 13,
    color: Colors.textMuted,
    fontStyle: 'italic',
  },
});
