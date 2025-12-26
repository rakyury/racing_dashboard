/**
 * @file rd_channel.c
 * @brief Racing Dashboard - Channel System Implementation
 */

#include "rd_channel.h"
#include <string.h>
#include <math.h>

// =============================================================================
// Private Definitions
// =============================================================================

#define MAX_CHANNELS            256
#define INVALID_CHANNEL_ID      0xFFFF

// =============================================================================
// Private Data
// =============================================================================

static struct {
    RD_ChannelDef_t defs[MAX_CHANNELS];
    RD_ChannelData_t data[MAX_CHANNELS];
    uint16_t count;
    bool initialized;
} s_channels;

// =============================================================================
// Private Functions
// =============================================================================

static int find_channel_index(uint16_t channel_id)
{
    for (uint16_t i = 0; i < s_channels.count; i++) {
        if (s_channels.defs[i].id == channel_id) {
            return i;
        }
    }
    return -1;
}

static float apply_analog_processing(const RD_AnalogInputConfig_t *cfg, uint32_t raw)
{
    float value;

    switch (cfg->input_type) {
        case RD_ANALOG_VOLTAGE:
            // Direct voltage: V = raw * scale + offset
            value = (float)raw * cfg->scale + cfg->offset;
            break;

        case RD_ANALOG_VOLTAGE_DIVIDER:
            // Voltage divider: already scaled in hardware
            value = (float)raw * cfg->scale + cfg->offset;
            break;

        case RD_ANALOG_CURRENT_0_20MA:
            // 4-20mA current loop
            value = (float)raw * cfg->scale + cfg->offset;
            break;

        case RD_ANALOG_THERMISTOR_NTC:
            // NTC thermistor using Steinhart-Hart (simplified Beta equation)
            if (raw > 0 && raw < cfg->max_raw) {
                float resistance = cfg->thermistor_pullup * ((float)raw / (cfg->max_raw - raw));
                float steinhart = logf(resistance / cfg->thermistor_r25) / cfg->thermistor_beta;
                steinhart += 1.0f / (25.0f + 273.15f);
                value = (1.0f / steinhart) - 273.15f;
            } else {
                value = NAN;
            }
            break;

        case RD_ANALOG_THERMISTOR_PTC:
            // PTC thermistor (linear approximation)
            value = (float)raw * cfg->scale + cfg->offset;
            break;

        case RD_ANALOG_RESISTANCE:
            // Direct resistance measurement
            if (raw > 0 && raw < cfg->max_raw) {
                value = cfg->thermistor_pullup * ((float)raw / (cfg->max_raw - raw));
            } else {
                value = NAN;
            }
            break;

        default:
            value = (float)raw * cfg->scale + cfg->offset;
            break;
    }

    // Clamp to valid range
    if (!isnan(value)) {
        if (value < cfg->min_value) value = cfg->min_value;
        if (value > cfg->max_value) value = cfg->max_value;
    }

    return value;
}

static float apply_digital_processing(const RD_DigitalInputConfig_t *cfg, uint32_t raw)
{
    float value;

    switch (cfg->input_type) {
        case RD_DIGITAL_ON_OFF:
            value = cfg->inverted ? (raw == 0 ? 1.0f : 0.0f) : (raw != 0 ? 1.0f : 0.0f);
            break;

        case RD_DIGITAL_FREQUENCY:
            // raw is frequency in mHz
            value = (float)raw / 1000.0f;
            if (value < cfg->min_frequency_hz) value = 0.0f;
            if (value > cfg->max_frequency_hz) value = cfg->max_frequency_hz;
            break;

        case RD_DIGITAL_PULSE_COUNT:
            value = (float)raw;
            break;

        case RD_DIGITAL_PWM_DUTY:
            // raw is duty cycle in 0.01% units
            value = (float)raw / 100.0f;
            break;

        case RD_DIGITAL_SPEED:
            // Convert frequency to speed using pulses_per_unit
            if (cfg->pulses_per_unit > 0) {
                float freq_hz = (float)raw / 1000.0f;
                value = freq_hz / cfg->pulses_per_unit;
            } else {
                value = 0.0f;
            }
            break;

        default:
            value = (float)raw;
            break;
    }

    return value;
}

static float apply_filter(float current, float new_value, float alpha)
{
    if (isnan(current)) {
        return new_value;
    }
    if (alpha <= 0.0f || alpha >= 1.0f) {
        return new_value;
    }
    return current * (1.0f - alpha) + new_value * alpha;
}

static float evaluate_logic(const RD_LogicConfig_t *cfg)
{
    float inputs[4] = {0};

    // Get input values
    for (uint8_t i = 0; i < cfg->input_count && i < 4; i++) {
        inputs[i] = RD_Channel_GetValue(cfg->input_channels[i]);
        if (isnan(inputs[i])) inputs[i] = 0.0f;
    }

    float result = 0.0f;

    switch (cfg->operation) {
        case RD_LOGIC_AND:
            result = 1.0f;
            for (uint8_t i = 0; i < cfg->input_count; i++) {
                if (inputs[i] == 0.0f) {
                    result = 0.0f;
                    break;
                }
            }
            break;

        case RD_LOGIC_OR:
            result = 0.0f;
            for (uint8_t i = 0; i < cfg->input_count; i++) {
                if (inputs[i] != 0.0f) {
                    result = 1.0f;
                    break;
                }
            }
            break;

        case RD_LOGIC_NOT:
            result = (inputs[0] == 0.0f) ? 1.0f : 0.0f;
            break;

        case RD_LOGIC_XOR:
            {
                int count = 0;
                for (uint8_t i = 0; i < cfg->input_count; i++) {
                    if (inputs[i] != 0.0f) count++;
                }
                result = (count % 2 == 1) ? 1.0f : 0.0f;
            }
            break;

        case RD_LOGIC_GT:
            result = (inputs[0] > cfg->parameters[0]) ? 1.0f : 0.0f;
            break;

        case RD_LOGIC_LT:
            result = (inputs[0] < cfg->parameters[0]) ? 1.0f : 0.0f;
            break;

        case RD_LOGIC_GTE:
            result = (inputs[0] >= cfg->parameters[0]) ? 1.0f : 0.0f;
            break;

        case RD_LOGIC_LTE:
            result = (inputs[0] <= cfg->parameters[0]) ? 1.0f : 0.0f;
            break;

        case RD_LOGIC_EQ:
            result = (fabsf(inputs[0] - cfg->parameters[0]) < 0.001f) ? 1.0f : 0.0f;
            break;

        case RD_LOGIC_RANGE:
            result = (inputs[0] >= cfg->parameters[0] && inputs[0] <= cfg->parameters[1]) ? 1.0f : 0.0f;
            break;

        case RD_LOGIC_MAP:
            // Linear interpolation: map input from [p0,p1] to [p2,p3]
            if (cfg->parameters[1] != cfg->parameters[0]) {
                float t = (inputs[0] - cfg->parameters[0]) / (cfg->parameters[1] - cfg->parameters[0]);
                result = cfg->parameters[2] + t * (cfg->parameters[3] - cfg->parameters[2]);
            }
            break;

        case RD_LOGIC_MIN:
            result = inputs[0];
            for (uint8_t i = 1; i < cfg->input_count; i++) {
                if (inputs[i] < result) result = inputs[i];
            }
            break;

        case RD_LOGIC_MAX:
            result = inputs[0];
            for (uint8_t i = 1; i < cfg->input_count; i++) {
                if (inputs[i] > result) result = inputs[i];
            }
            break;

        case RD_LOGIC_AVG:
            result = 0.0f;
            for (uint8_t i = 0; i < cfg->input_count; i++) {
                result += inputs[i];
            }
            if (cfg->input_count > 0) {
                result /= cfg->input_count;
            }
            break;

        case RD_LOGIC_SUM:
            result = 0.0f;
            for (uint8_t i = 0; i < cfg->input_count; i++) {
                result += inputs[i];
            }
            break;

        case RD_LOGIC_DIFF:
            result = inputs[0] - inputs[1];
            break;

        case RD_LOGIC_MUL:
            result = inputs[0] * inputs[1];
            break;

        case RD_LOGIC_DIV:
            if (inputs[1] != 0.0f) {
                result = inputs[0] / inputs[1];
            } else {
                result = NAN;
            }
            break;

        case RD_LOGIC_ABS:
            result = fabsf(inputs[0]);
            break;

        case RD_LOGIC_CLAMP:
            result = inputs[0];
            if (result < cfg->parameters[0]) result = cfg->parameters[0];
            if (result > cfg->parameters[1]) result = cfg->parameters[1];
            break;

        case RD_LOGIC_DEADBAND:
            if (fabsf(inputs[0]) < cfg->parameters[0]) {
                result = 0.0f;
            } else {
                result = inputs[0];
            }
            break;

        case RD_LOGIC_HYSTERESIS:
            // Simple hysteresis: parameters[0]=low, parameters[1]=high
            // Uses parameters[2] to store state
            if (inputs[0] >= cfg->parameters[1]) {
                result = 1.0f;
            } else if (inputs[0] <= cfg->parameters[0]) {
                result = 0.0f;
            } else {
                result = cfg->parameters[2];  // Keep previous state
            }
            break;

        case RD_LOGIC_RATE_OF_CHANGE:
            // This would need state - simplified version
            result = inputs[0];
            break;

        default:
            result = inputs[0];
            break;
    }

    return result;
}

// =============================================================================
// Public API Implementation
// =============================================================================

RD_Error_t RD_Channel_Init(void)
{
    memset(&s_channels, 0, sizeof(s_channels));
    s_channels.initialized = true;
    return RD_OK;
}

void RD_Channel_Deinit(void)
{
    memset(&s_channels, 0, sizeof(s_channels));
}

RD_Error_t RD_Channel_Register(const RD_ChannelDef_t *def)
{
    if (!s_channels.initialized) {
        return RD_ERR_NOT_INITIALIZED;
    }

    if (!def) {
        return RD_ERR_INVALID_PARAM;
    }

    // Check if channel already exists
    if (find_channel_index(def->id) >= 0) {
        return RD_ERR_ALREADY_EXISTS;
    }

    // Check capacity
    if (s_channels.count >= MAX_CHANNELS) {
        return RD_ERR_NO_MEMORY;
    }

    // Add channel
    uint16_t idx = s_channels.count;
    memcpy(&s_channels.defs[idx], def, sizeof(RD_ChannelDef_t));

    // Initialize data
    s_channels.data[idx].value.value = NAN;
    s_channels.data[idx].value.valid = false;
    s_channels.data[idx].value.timestamp = 0;
    s_channels.data[idx].raw_value = NAN;
    s_channels.data[idx].update_count = 0;
    s_channels.data[idx].error_count = 0;

    s_channels.count++;

    return RD_OK;
}

RD_Error_t RD_Channel_Unregister(uint16_t channel_id)
{
    if (!s_channels.initialized) {
        return RD_ERR_NOT_INITIALIZED;
    }

    int idx = find_channel_index(channel_id);
    if (idx < 0) {
        return RD_ERR_NOT_FOUND;
    }

    // Remove by shifting remaining channels
    for (uint16_t i = idx; i < s_channels.count - 1; i++) {
        s_channels.defs[i] = s_channels.defs[i + 1];
        s_channels.data[i] = s_channels.data[i + 1];
    }

    s_channels.count--;

    return RD_OK;
}

float RD_Channel_GetValue(uint16_t channel_id)
{
    int idx = find_channel_index(channel_id);
    if (idx < 0) {
        return NAN;
    }

    return s_channels.data[idx].value.value;
}

RD_Error_t RD_Channel_GetValueEx(uint16_t channel_id, RD_ChannelValue_t *value)
{
    if (!value) {
        return RD_ERR_INVALID_PARAM;
    }

    int idx = find_channel_index(channel_id);
    if (idx < 0) {
        return RD_ERR_NOT_FOUND;
    }

    memcpy(value, &s_channels.data[idx].value, sizeof(RD_ChannelValue_t));
    return RD_OK;
}

RD_Error_t RD_Channel_SetValue(uint16_t channel_id, float value)
{
    int idx = find_channel_index(channel_id);
    if (idx < 0) {
        return RD_ERR_NOT_FOUND;
    }

    s_channels.data[idx].value.value = value;
    s_channels.data[idx].value.valid = !isnan(value);
    // Note: timestamp should be set by caller or system
    s_channels.data[idx].update_count++;

    return RD_OK;
}

RD_Error_t RD_Channel_UpdateRaw(uint16_t channel_id, uint32_t raw_value)
{
    int idx = find_channel_index(channel_id);
    if (idx < 0) {
        return RD_ERR_NOT_FOUND;
    }

    RD_ChannelDef_t *def = &s_channels.defs[idx];
    RD_ChannelData_t *data = &s_channels.data[idx];

    if (!def->enabled) {
        return RD_ERR_DISABLED;
    }

    float processed_value = NAN;

    switch (def->type) {
        case RD_CH_TYPE_ANALOG_IN:
            processed_value = apply_analog_processing(&def->config.analog, raw_value);
            // Apply filter
            if (def->config.analog.filter_alpha > 0.0f) {
                processed_value = apply_filter(data->value.value, processed_value,
                                              def->config.analog.filter_alpha);
            }
            break;

        case RD_CH_TYPE_DIGITAL_IN:
            processed_value = apply_digital_processing(&def->config.digital, raw_value);
            break;

        default:
            return RD_ERR_INVALID_TYPE;
    }

    data->raw_value = (float)raw_value;
    data->value.value = processed_value;
    data->value.valid = !isnan(processed_value);
    data->update_count++;

    return RD_OK;
}

bool RD_Channel_Exists(uint16_t channel_id)
{
    return find_channel_index(channel_id) >= 0;
}

bool RD_Channel_IsValid(uint16_t channel_id)
{
    int idx = find_channel_index(channel_id);
    if (idx < 0) {
        return false;
    }
    return s_channels.data[idx].value.valid;
}

const RD_ChannelDef_t* RD_Channel_GetDef(uint16_t channel_id)
{
    int idx = find_channel_index(channel_id);
    if (idx < 0) {
        return NULL;
    }
    return &s_channels.defs[idx];
}

const char* RD_Channel_GetName(uint16_t channel_id)
{
    const RD_ChannelDef_t *def = RD_Channel_GetDef(channel_id);
    return def ? def->name : "Unknown";
}

const char* RD_Channel_GetUnits(uint16_t channel_id)
{
    const RD_ChannelDef_t *def = RD_Channel_GetDef(channel_id);
    return def ? def->units : "";
}

uint16_t RD_Channel_FindByName(const char *name)
{
    if (!name) {
        return INVALID_CHANNEL_ID;
    }

    for (uint16_t i = 0; i < s_channels.count; i++) {
        if (strcmp(s_channels.defs[i].name, name) == 0) {
            return s_channels.defs[i].id;
        }
    }

    return INVALID_CHANNEL_ID;
}

void RD_Channel_Process(uint32_t delta_ms)
{
    (void)delta_ms;

    // Process logic channels
    for (uint16_t i = 0; i < s_channels.count; i++) {
        RD_ChannelDef_t *def = &s_channels.defs[i];

        if (!def->enabled) continue;

        if (def->type == RD_CH_TYPE_LOGIC) {
            float result = evaluate_logic(&def->config.logic);
            s_channels.data[i].value.value = result;
            s_channels.data[i].value.valid = !isnan(result);
            s_channels.data[i].update_count++;
        }
    }
}

uint16_t RD_Channel_GetCount(void)
{
    return s_channels.count;
}

void RD_Channel_ForEach(bool (*callback)(const RD_ChannelDef_t *def, void *user_data), void *user_data)
{
    if (!callback) return;

    for (uint16_t i = 0; i < s_channels.count; i++) {
        if (!callback(&s_channels.defs[i], user_data)) {
            break;
        }
    }
}
