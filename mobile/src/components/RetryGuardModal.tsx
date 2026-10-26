import React from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity } from 'react-native';
import { Colors } from '../theme/colors';
import { Ionicons } from '@expo/vector-icons';

interface RetryGuardModalProps {
  visible: boolean;
  onClose: () => void;
  onViewPrevious: (txId: string) => void;
  onContinueAnyway: () => void;
  warningMessage?: string;
  existingTransactionId?: string;
  existingAmount?: number;
  elapsedMinutes?: number;
}

export const RetryGuardModal: React.FC<RetryGuardModalProps> = ({
  visible,
  onClose,
  onViewPrevious,
  onContinueAnyway,
  warningMessage,
  existingTransactionId,
  existingAmount = 4000,
  elapsedMinutes = 1,
}) => {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.cardContainer}>
          {/* Header icon & badge */}
          <View style={styles.iconCircle}>
            <Ionicons name="shield-half" size={32} color={Colors.warningOrange} />
          </View>
          
          <View style={styles.badgeRow}>
            <View style={styles.alertBadge}>
              <Text style={styles.alertBadgeText}>RETRYGUARD DUPLICATE PROTECTION</Text>
            </View>
          </View>

          <Text style={styles.titleText}>Possible Duplicate Payment</Text>

          <Text style={styles.messageText}>
            {warningMessage ||
              `Your previous ₹${existingAmount.toLocaleString('en-IN')} payment to this merchant is still unconfirmed (${elapsedMinutes} min ago).`}
          </Text>

          {/* Details Box */}
          <View style={styles.detailsBox}>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Unresolved Amount:</Text>
              <Text style={styles.detailValue}>₹{existingAmount.toLocaleString('en-IN')}</Text>
            </View>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Elapsed Time:</Text>
              <Text style={styles.detailValue}>{elapsedMinutes} minute(s) ago</Text>
            </View>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Current Status:</Text>
              <Text style={[styles.detailValue, { color: Colors.warningOrange }]}>Investigation Active</Text>
            </View>
          </View>

          <Text style={styles.adviceText}>
            Paying again right now may result in a double bank debit if your original transaction settles.
          </Text>

          {/* Actions */}
          <View style={styles.actionColumn}>
            {existingTransactionId && (
              <TouchableOpacity
                style={styles.primaryBtn}
                onPress={() => onViewPrevious(existingTransactionId)}
                activeOpacity={0.85}
              >
                <Ionicons name="search" size={16} color={Colors.textWhite} style={{ marginRight: 6 }} />
                <Text style={styles.primaryBtnText}>Track & Resolve Previous Payment</Text>
              </TouchableOpacity>
            )}

            <TouchableOpacity
              style={styles.secondaryBtn}
              onPress={onClose}
              activeOpacity={0.8}
            >
              <Text style={styles.secondaryBtnText}>Cancel and Check Later</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.tertiaryBtn}
              onPress={onContinueAnyway}
              activeOpacity={0.7}
            >
              <Text style={styles.tertiaryBtnText}>I understand the risk, pay anyway</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  cardContainer: {
    backgroundColor: Colors.cardBackground,
    borderRadius: 20,
    padding: 24,
    width: '100%',
    maxWidth: 380,
    alignItems: 'center',
    elevation: 8,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
  },
  iconCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: Colors.warningLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  badgeRow: {
    marginBottom: 8,
  },
  alertBadge: {
    backgroundColor: 'rgba(255, 153, 0, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  alertBadgeText: {
    color: Colors.warningOrange,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  titleText: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 8,
    textAlign: 'center',
  },
  messageText: {
    fontSize: 13,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 16,
  },
  detailsBox: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 12,
    padding: 12,
    width: '100%',
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  detailLabel: {
    fontSize: 12,
    color: Colors.textSecondary,
  },
  detailValue: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
  adviceText: {
    fontSize: 11,
    color: Colors.textMuted,
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 16,
  },
  actionColumn: {
    width: '100%',
  },
  primaryBtn: {
    backgroundColor: Colors.paytmBlue,
    borderRadius: 12,
    paddingVertical: 13,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  primaryBtnText: {
    color: Colors.textWhite,
    fontSize: 14,
    fontWeight: '700',
  },
  secondaryBtn: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 12,
    paddingVertical: 11,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 8,
  },
  secondaryBtnText: {
    color: Colors.textPrimary,
    fontSize: 13,
    fontWeight: '600',
  },
  tertiaryBtn: {
    paddingVertical: 8,
    alignItems: 'center',
  },
  tertiaryBtnText: {
    color: Colors.errorRed,
    fontSize: 11,
    fontWeight: '500',
    textDecorationLine: 'underline',
  },
});
