import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Colors } from '../theme/colors';
import { Ionicons } from '@expo/vector-icons';

interface FloatingAskRaahProps {
  onPress: () => void;
  hasUnread?: boolean;
}

export const FloatingAskRaah: React.FC<FloatingAskRaahProps> = ({
  onPress,
  hasUnread = true,
}) => {
  return (
    <TouchableOpacity
      style={styles.floatingButton}
      onPress={onPress}
      activeOpacity={0.85}
    >
      <View style={styles.innerGlow}>
        <Ionicons name="sparkles" size={24} color={Colors.textWhite} />
      </View>
      <Text style={styles.btnLabel}>Ask Raah</Text>

      {hasUnread && (
        <View style={styles.badgePulse}>
          <View style={styles.badgeDot} />
        </View>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  floatingButton: {
    position: 'absolute',
    bottom: 24,
    right: 20,
    backgroundColor: Colors.paytmBlue,
    borderRadius: 30,
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 16,
    elevation: 8,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    borderWidth: 1.5,
    borderColor: Colors.paytmLightBlue,
    zIndex: 999,
  },
  innerGlow: {
    marginRight: 8,
  },
  btnLabel: {
    color: Colors.textWhite,
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.4,
  },
  badgePulse: {
    position: 'absolute',
    top: -3,
    right: -3,
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: 'rgba(0, 186, 242, 0.4)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.paytmLightBlue,
  },
});
