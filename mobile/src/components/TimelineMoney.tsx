import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Ionicons } from '@expo/vector-icons';

export interface MoneyEvent {
  id: string;
  event_type: string;
  source: string;
  title: string;
  description?: string;
  verification_status: string;
  is_synthetic: boolean;
  event_timestamp: string;
}

interface TimelineMoneyProps {
  events: MoneyEvent[];
}

export const TimelineMoney: React.FC<TimelineMoneyProps> = ({ events }) => {
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'INITIATED':
        return 'qr-code-outline';
      case 'DEBIT_REPORTED':
        return 'card-outline';
      case 'GATEWAY_PROCESSING':
        return 'git-network-outline';
      case 'BENEFICIARY_CONFIRMED':
        return 'checkmark-done-circle';
      case 'BENEFICIARY_PENDING':
        return 'time-outline';
      case 'PAYMENT_FAILED':
        return 'close-circle-outline';
      case 'REVERSAL_INITIATED':
        return 'refresh-circle-outline';
      case 'REVERSAL_COMPLETED':
        return 'wallet-outline';
      default:
        return 'ellipse';
    }
  };

  const getEventColor = (type: string, status: string) => {
    if (type === 'REVERSAL_COMPLETED' || type === 'BENEFICIARY_CONFIRMED') {
      return Colors.successGreen;
    }
    if (type === 'PAYMENT_FAILED') {
      return Colors.errorRed;
    }
    if (type === 'BENEFICIARY_PENDING' || type === 'REVERSAL_INITIATED') {
      return Colors.warningOrange;
    }
    return Colors.paytmBlue;
  };

  const formatTimestamp = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return isoString;
    }
  };

  if (!events || events.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>No verified transaction signals recorded yet.</Text>
      </View>
    );
  }

  return (
    <View style={styles.timelineContainer}>
      <View style={styles.sectionHeader}>
        <View style={styles.headerIconCircle}>
          <Ionicons name="cash-outline" size={16} color={Colors.paytmBlue} />
        </View>
        <Text style={styles.sectionTitle}>TIMELINE A: MONEY JOURNEY</Text>
        <View style={styles.verifiedCountBadge}>
          <Text style={styles.verifiedCountText}>{events.length} Events</Text>
        </View>
      </View>

      <Text style={styles.timelineSubtitle}>
        Strictly reflects evidence received from payment switch, banks, and merchant backend.
      </Text>

      {events.map((ev, index) => {
        const isLast = index === events.length - 1;
        const color = getEventColor(ev.event_type, ev.verification_status);

        return (
          <View key={ev.id || index} style={styles.eventRow}>
            {/* Left timeline line & icon node */}
            <View style={styles.nodeColumn}>
              <View style={[styles.iconNode, { borderColor: color }]}>
                <Ionicons name={getEventIcon(ev.event_type) as any} size={15} color={color} />
              </View>
              {!isLast && <View style={styles.verticalLine} />}
            </View>

            {/* Right event content */}
            <View style={[styles.eventContent, isLast && styles.lastEventContent]}>
              <View style={styles.eventTitleRow}>
                <Text style={styles.eventTitle}>{ev.title}</Text>
                <Text style={styles.timestampText}>{formatTimestamp(ev.event_timestamp)}</Text>
              </View>

              {ev.description && (
                <Text style={styles.eventDescription}>{ev.description}</Text>
              )}

              {/* Source & Verification Badges */}
              <View style={styles.badgeRow}>
                <View style={styles.sourceBadge}>
                  <Text style={styles.sourceBadgeText}>SOURCE: {ev.source}</Text>
                </View>
                <View style={[styles.statusBadge, ev.verification_status === 'VERIFIED' ? styles.statusVerified : styles.statusPending]}>
                  <Text style={[styles.statusBadgeText, ev.verification_status === 'VERIFIED' ? styles.textVerified : styles.textPending]}>
                    {ev.verification_status}
                  </Text>
                </View>
              </View>
            </View>
          </View>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  timelineContainer: {
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
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  headerIconCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.paytmCyan,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: Colors.paytmDeepBlue,
    letterSpacing: 0.6,
    flex: 1,
  },
  verifiedCountBadge: {
    backgroundColor: Colors.surfaceLight,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  verifiedCountText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  timelineSubtitle: {
    fontSize: 11,
    color: Colors.textMuted,
    marginBottom: 16,
    lineHeight: 15,
  },
  eventRow: {
    flexDirection: 'row',
  },
  nodeColumn: {
    alignItems: 'center',
    width: 32,
    marginRight: 10,
  },
  iconNode: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: Colors.cardBackground,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    zIndex: 2,
  },
  verticalLine: {
    width: 2,
    flex: 1,
    backgroundColor: Colors.borderLight,
    marginVertical: 4,
  },
  eventContent: {
    flex: 1,
    paddingBottom: 20,
  },
  lastEventContent: {
    paddingBottom: 4,
  },
  eventTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  eventTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.textPrimary,
    flex: 1,
  },
  timestampText: {
    fontSize: 10,
    color: Colors.textMuted,
    fontWeight: '500',
  },
  eventDescription: {
    fontSize: 11.5,
    color: Colors.textSecondary,
    lineHeight: 16,
    marginTop: 3,
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 6,
    gap: 6,
  },
  sourceBadge: {
    backgroundColor: Colors.surfaceLight,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    borderWidth: 0.8,
    borderColor: Colors.border,
  },
  sourceBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: Colors.textSecondary,
    letterSpacing: 0.3,
  },
  statusBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  statusVerified: {
    backgroundColor: Colors.successLight,
  },
  statusPending: {
    backgroundColor: Colors.warningLight,
  },
  statusBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  textVerified: {
    color: Colors.successGreen,
  },
  textPending: {
    color: Colors.warningOrange,
  },
  emptyContainer: {
    padding: 20,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 12,
    color: Colors.textMuted,
    fontStyle: 'italic',
  },
});
