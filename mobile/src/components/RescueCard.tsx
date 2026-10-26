import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Colors } from '../theme/colors';
import { Ionicons } from '@expo/vector-icons';

export interface RescueCardData {
  transaction_id: string;
  case_number?: string;
  amount: number;
  merchant_name: string;
  merchant_category: string;
  merchant_upi: string;
  last_verified_status: string;
  known_failure_evidence: string;
  what_remains_unknown: string;
  regulatory_deadline_title: string;
  regulatory_deadline_date?: string;
  regulatory_explanation: string;
  compensation_rate: string;
  last_checked_at?: string;
  next_scheduled_check?: string;
  latest_ai_action: string;
  assigned_agent: string;
  correlated_incident_number?: string;
}

interface RescueCardProps {
  data: RescueCardData;
  onTriggerCheck?: () => void;
  checking?: boolean;
}

export const RescueCard: React.FC<RescueCardProps> = ({
  data,
  onTriggerCheck,
  checking = false,
}) => {
  const isResolved = data.last_verified_status === 'RESOLVED' || data.last_verified_status === 'REVERSED';
  const isFailed = data.last_verified_status === 'FAILED';

  const formatTime = (isoString?: string) => {
    if (!isoString) return 'Pending check';
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return isoString;
    }
  };

  const formatDate = (isoString?: string) => {
    if (!isoString) return 'Calculating...';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString([], { day: '2-digit', month: 'short', year: 'numeric' });
    } catch {
      return isoString;
    }
  };

  return (
    <View style={styles.card}>
      {/* Top Banner: Status & Case ID */}
      <View style={styles.topHeader}>
        <View style={styles.caseBadge}>
          <Ionicons name="shield-checkmark" size={14} color={Colors.paytmLightBlue} style={{ marginRight: 4 }} />
          <Text style={styles.caseBadgeText}>{data.case_number || 'INVESTIGATION ACTIVE'}</Text>
        </View>

        <View style={[styles.statusBadge, isResolved ? styles.badgeSuccess : styles.badgeAmber]}>
          <Text style={[styles.statusText, isResolved ? styles.textSuccess : styles.textAmber]}>
            {data.last_verified_status}
          </Text>
        </View>
      </View>

      {/* Amount & Merchant */}
      <View style={styles.amountSection}>
        <Text style={styles.amountLabel}>TRANSACTION AMOUNT</Text>
        <Text style={styles.amountValue}>₹{data.amount.toLocaleString('en-IN')}</Text>
        <View style={styles.merchantRow}>
          <Ionicons name="cart-outline" size={16} color={Colors.textSecondary} style={{ marginRight: 6 }} />
          <Text style={styles.merchantName}>{data.merchant_name}</Text>
          <Text style={styles.merchantUpi}>({data.merchant_upi})</Text>
        </View>
      </View>

      {/* Pulse Incident Link Banner if correlated */}
      {data.correlated_incident_number && (
        <View style={styles.incidentLinkBanner}>
          <Ionicons name="flash" size={16} color={Colors.accentPurple} style={{ marginRight: 6 }} />
          <Text style={styles.incidentLinkText}>
            Linked to Pulse Operations Incident {data.correlated_incident_number} (Cluster Timeout)
          </Text>
        </View>
      )}

      {/* Verified Facts vs Unknowns Box */}
      <View style={styles.factsContainer}>
        {/* Known Evidence */}
        <View style={styles.factItem}>
          <View style={styles.factIconWrapGreen}>
            <Ionicons name="checkmark-circle" size={16} color={Colors.successGreen} />
          </View>
          <View style={styles.factContent}>
            <Text style={styles.factHeading}>VERIFIED EVIDENCE</Text>
            <Text style={styles.factDescription}>{data.known_failure_evidence}</Text>
          </View>
        </View>

        {/* What remains unknown */}
        <View style={styles.factItem}>
          <View style={styles.factIconWrapAmber}>
            <Ionicons name="help-circle" size={16} color={Colors.warningOrange} />
          </View>
          <View style={styles.factContent}>
            <Text style={styles.factHeading}>CURRENT UNCERTAINTY</Text>
            <Text style={styles.factDescription}>{data.what_remains_unknown}</Text>
          </View>
        </View>
      </View>

      {/* Regulatory Resolution Policy Box */}
      <View style={styles.regulatoryBox}>
        <View style={styles.regHeader}>
          <Ionicons name="document-text-outline" size={16} color={Colors.paytmBlue} style={{ marginRight: 6 }} />
          <Text style={styles.regTitle}>RBI Failed-Transaction Turnaround (TAT)</Text>
        </View>
        
        <View style={styles.regDetailsRow}>
          <View style={styles.regCol}>
            <Text style={styles.regSublabel}>Regulatory Deadline:</Text>
            <Text style={styles.regDeadlineDate}>
              {data.regulatory_deadline_date ? formatDate(data.regulatory_deadline_date) : 'T+5 Days'}
            </Text>
          </View>
          <View style={styles.regCol}>
            <Text style={styles.regSublabel}>Statutory Compensation:</Text>
            <Text style={styles.regCompRate}>{data.compensation_rate}</Text>
          </View>
        </View>

        <Text style={styles.regDisclaimer}>
          Note: Established under RBI Circular DPSS.CO.PD No.629. This is a regulatory resolution deadline, not a guaranteed credit timestamp.
        </Text>
      </View>

      {/* Monitoring state footer */}
      <View style={styles.footerRow}>
        <View style={styles.timingCol}>
          <Text style={styles.footerLabel}>Last Checked: {formatTime(data.last_checked_at)}</Text>
          {data.next_scheduled_check && (
            <Text style={styles.footerLabelNext}>Next Scheduled: {formatTime(data.next_scheduled_check)}</Text>
          )}
        </View>

        {onTriggerCheck && (
          <TouchableOpacity
            style={[styles.recheckButton, checking && styles.recheckButtonDisabled]}
            onPress={onTriggerCheck}
            disabled={checking}
            activeOpacity={0.8}
          >
            <Ionicons
              name={checking ? 'reload' : 'play-forward'}
              size={14}
              color={Colors.textWhite}
              style={{ marginRight: 4 }}
            />
            <Text style={styles.recheckBtnText}>{checking ? 'Querying...' : 'Verify Now'}</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Latest Agent Action ticker */}
      <View style={styles.agentActionRow}>
        <Ionicons name="hardware-chip-outline" size={14} color={Colors.paytmLightBlue} style={{ marginRight: 6 }} />
        <Text style={styles.agentActionText} numberOfLines={2}>
          Latest Action: {data.latest_ai_action}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.cardBackground,
    borderRadius: 18,
    padding: 18,
    marginHorizontal: 16,
    marginVertical: 10,
    elevation: 3,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  topHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  caseBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.paytmCyan,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  caseBadgeText: {
    color: Colors.paytmBlue,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  badgeAmber: {
    backgroundColor: Colors.warningLight,
  },
  badgeSuccess: {
    backgroundColor: Colors.successLight,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  textAmber: {
    color: Colors.warningOrange,
  },
  textSuccess: {
    color: Colors.successGreen,
  },
  amountSection: {
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.borderLight,
    marginBottom: 14,
  },
  amountLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.textMuted,
    letterSpacing: 0.8,
  },
  amountValue: {
    fontSize: 30,
    fontWeight: '800',
    color: Colors.textPrimary,
    marginVertical: 2,
  },
  merchantRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  merchantName: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textPrimary,
    marginRight: 4,
  },
  merchantUpi: {
    fontSize: 12,
    color: Colors.textMuted,
  },
  incidentLinkBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(124, 58, 237, 0.08)',
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: 8,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: 'rgba(124, 58, 237, 0.25)',
  },
  incidentLinkText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.accentPurple,
    flex: 1,
  },
  factsContainer: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 12,
    padding: 12,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: Colors.borderLight,
  },
  factItem: {
    flexDirection: 'row',
    marginVertical: 4,
  },
  factIconWrapGreen: {
    marginRight: 8,
    marginTop: 2,
  },
  factIconWrapAmber: {
    marginRight: 8,
    marginTop: 2,
  },
  factContent: {
    flex: 1,
  },
  factHeading: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.textSecondary,
    letterSpacing: 0.5,
  },
  factDescription: {
    fontSize: 12,
    color: Colors.textPrimary,
    lineHeight: 16,
    marginTop: 1,
  },
  regulatoryBox: {
    backgroundColor: Colors.paytmLightCyan,
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: 'rgba(0, 186, 242, 0.3)',
    marginBottom: 14,
  },
  regHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  regTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.paytmBlue,
  },
  regDetailsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  regCol: {
    flex: 1,
  },
  regSublabel: {
    fontSize: 10,
    color: Colors.textSecondary,
  },
  regDeadlineDate: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.paytmBlue,
    marginTop: 1,
  },
  regCompRate: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginTop: 1,
  },
  regDisclaimer: {
    fontSize: 9.5,
    color: Colors.textMuted,
    lineHeight: 13,
    marginTop: 6,
    fontStyle: 'italic',
  },
  footerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 4,
    paddingBottom: 8,
  },
  timingCol: {
    flex: 1,
  },
  footerLabel: {
    fontSize: 10,
    color: Colors.textSecondary,
  },
  footerLabelNext: {
    fontSize: 10,
    color: Colors.paytmLightBlue,
    fontWeight: '600',
    marginTop: 2,
  },
  recheckButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.paytmBlue,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 8,
  },
  recheckButtonDisabled: {
    opacity: 0.6,
  },
  recheckBtnText: {
    color: Colors.textWhite,
    fontSize: 12,
    fontWeight: '700',
  },
  agentActionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 41, 112, 0.05)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    marginTop: 4,
  },
  agentActionText: {
    fontSize: 11,
    color: Colors.paytmNavy,
    fontWeight: '500',
    flex: 1,
  },
});
